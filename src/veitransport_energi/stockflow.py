"""Bestand–strøm-modell per drivlinje.

Modellkjernen i fase 3. Identiteten er

    bestand[f, t] = bestand[f, t-1] + tilgang[f, t] - nettoavgang[f, t]

der nettoavgangen modelleres som en rate ganger foregående års bestand:

    nettoavgang[f, t] = rate[f] * bestand[f, t-1]

Dette er den enkleste spesifikasjonen som lukker identiteten, og designporten
krevde at den prøves før en kohort- eller overlevelsesmodell tas inn (M3):
en mer avansert metode skal bare brukes når den løser et dokumentert problem.

Ratene kalibreres på historiske år og valideres på senere år som ikke inngikk i
kalibreringen. Kalibrerings- og valideringsvinduet er alltid tidsmessig atskilt,
slik at valideringen ikke ser sitt eget svar.

To oppdelinger støttes, fordi kildene tillater ulik detalj i ulike perioder:

    grov  — elektrisitet mot ikke-elektrisk, fra 2009, tilgang fra 14020
    fin   — bensin, diesel, elektrisitet, hybrid og annet, fra 2019,
            tilgang fra 12906

Den grove gir lang historikk å validere mot; den fine gir den oppdelingen
framskrivingen trenger.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .datasets import read_extract

STOCK_VARIABLE = {"personbiler": "Personbil1", "varebiler": "Varebil4"}

# grov oppdeling: bestandskoder i 07849 og tilgangskoder i 14020
COARSE = {
    "elektrisitet": {"bestand": ["5"], "tilgang": ["19"]},
    "ikke_elektrisk": {"bestand": ["1", "2", "3", "4", "6"], "tilgang": ["20", "21", "6"]},
}
COARSE_INFLOW_VARIABLE = {"personbiler": "Personbiler", "varebiler": "VareCampBiler"}

# fin oppdeling: bestandskoder i 07849 og tilgangskoder i 12906
FINE = {
    "bensin": {"bestand": ["1"], "tilgang": ["1"]},
    "diesel": {"bestand": ["2"], "tilgang": ["2"]},
    "elektrisitet": {"bestand": ["5"], "tilgang": ["5", "13"]},
    "hybrid": {"bestand": ["6"], "tilgang": ["14", "15", "16", "17"]},
    "annet": {"bestand": ["3", "4"], "tilgang": ["3", "4", "6"]},
}
FINE_INFLOW_VARIABLE = {"personbiler": "Personbil1", "varebiler": "Varebil4"}


@dataclass(frozen=True)
class ModelData:
    """Observert bestand og tilgang per drivlinje og år, klar for modellen."""
    stock: pd.DataFrame     # index: år (str), kolonner: drivlinje
    inflow: pd.DataFrame    # samme form
    resolution: str


def load_model_data(gruppe: str, resolution: str = "fin") -> ModelData:
    if gruppe not in STOCK_VARIABLE:
        raise KeyError(f"ukjent gruppe '{gruppe}'; kjente: {list(STOCK_VARIABLE)}")
    if resolution not in ("grov", "fin"):
        raise ValueError("resolution må være 'grov' eller 'fin'")

    st = read_extract("stock_07849")
    s = st[st["ContentsCode"] == STOCK_VARIABLE[gruppe]]

    if resolution == "fin":
        kart, kilde, variabel = FINE, "firstreg_12906", FINE_INFLOW_VARIABLE[gruppe]
        fr = read_extract(kilde)
        fr = fr[fr["ContentsCode"] == variabel].copy()
        fr["aar"] = fr["Tid"].astype(str)
    else:
        kart, kilde, variabel = COARSE, "firstreg_14020", COARSE_INFLOW_VARIABLE[gruppe]
        fr = read_extract(kilde)
        fr = fr[fr["ContentsCode"] == variabel].copy()
        fr["aar"] = fr["Tid"].astype(str).str[:4]
        hele = fr.groupby("aar")["Tid"].nunique().pipe(lambda x: x[x == 12].index)
        fr = fr[fr["aar"].isin(hele)]

    stock, inflow = {}, {}
    for drivlinje, koder in kart.items():
        stock[drivlinje] = (s[s["DrivstoffType"].isin(koder["bestand"])]
                            .groupby("Tid")["value"].sum())
        inflow[drivlinje] = (fr[fr["DrivstoffType"].isin(koder["tilgang"])]
                             .groupby("aar")["value"].sum())
    sdf = pd.DataFrame(stock).sort_index()
    idf = pd.DataFrame(inflow).sort_index()
    felles = sdf.index.intersection(idf.index)
    return ModelData(stock=sdf, inflow=idf.loc[felles], resolution=resolution)


def calibrate_rates(data: ModelData, years: list[str]) -> pd.Series:
    """Gjennomsnittlig avgangsrate per drivlinje over de oppgitte kalibreringsårene."""
    rater = {}
    for drivlinje in data.stock.columns:
        verdier = []
        for aar in years:
            forrige = str(int(aar) - 1)
            if forrige not in data.stock.index or aar not in data.inflow.index:
                continue
            b0 = data.stock.loc[forrige, drivlinje]
            if not b0:
                continue
            netto = b0 + data.inflow.loc[aar, drivlinje] - data.stock.loc[aar, drivlinje]
            verdier.append(netto / b0)
        if not verdier:
            raise ValueError(f"ingen kalibreringsår med data for {drivlinje}")
        rater[drivlinje] = sum(verdier) / len(verdier)
    return pd.Series(rater, name="avgangsrate")


def run(data: ModelData, rates: pd.Series, start_year: str, end_year: str) -> pd.DataFrame:
    """Rull bestanden framover fra observert starttilstand med observert tilgang.

    Brukes til backcast: tilgangen er observert, slik at det som faktisk testes,
    er avgangsleddet — ikke modellens evne til å gjette nyregistreringer.
    """
    if start_year not in data.stock.index:
        raise KeyError(f"starttilstand mangler for {start_year}")
    tilstand = data.stock.loc[start_year].copy()
    rader = {start_year: tilstand.copy()}
    for aar_int in range(int(start_year) + 1, int(end_year) + 1):
        aar = str(aar_int)
        if aar not in data.inflow.index:
            break
        tilstand = tilstand + data.inflow.loc[aar] - rates * tilstand
        rader[aar] = tilstand.copy()
    return pd.DataFrame(rader).T


def backcast(gruppe: str, resolution: str, calib_years: list[str],
             start_year: str, end_year: str) -> pd.DataFrame:
    """Kjør modellen over et valideringsvindu og sammenlign med observert bestand.

    Kalibreringsårene skal ligge før valideringsvinduet; funksjonen nekter ellers,
    fordi resultatet da ville vært informasjonslekkasje framfor validering.
    """
    if max(int(a) for a in calib_years) > int(start_year):
        raise ValueError(
            "kalibreringsår ligger inne i valideringsvinduet — det ville vært lekkasje"
        )
    data = load_model_data(gruppe, resolution)
    rater = calibrate_rates(data, calib_years)
    modellert = run(data, rater, start_year, end_year)
    rows = []
    for aar in modellert.index:
        if aar not in data.stock.index:
            continue
        for drivlinje in modellert.columns:
            obs = data.stock.loc[aar, drivlinje]
            mod = modellert.loc[aar, drivlinje]
            rows.append({
                "gruppe": gruppe, "oppdeling": resolution, "drivlinje": drivlinje,
                "periode": aar, "observert": obs, "modellert": mod,
                "avvik": mod - obs,
                "avvik_pct": (mod - obs) / obs * 100 if obs else float("nan"),
                "horisont_aar": int(aar) - int(start_year),
                "kalibrert_paa": ",".join(calib_years),
                "avgangsrate": rater[drivlinje],
            })
    return pd.DataFrame(rows)
