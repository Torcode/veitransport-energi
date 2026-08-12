"""Kohortmodell for kjøretøybestanden.

Bakgrunnen er dokumentert i D-0025 og D-0026. Den enkle rate-modellen bommer
systematisk på ti års horisont fordi avgangsraten ikke er stasjonær når flåtens
alderssammensetning endrer seg, og aldersgruppene i SSB-tabell 08581 kan ikke
brukes til å lese overlevelsen direkte — de har et udokumentert
definisjonsbrudd i 2024 og ingen drivstoffdeling.

Denne modellen går motsatt vei. Aldersfordelingen bygges fra
tilgangshistorikken, som er observert per år tilbake til 1995, og
overlevelseskurven estimeres ved å minimere avviket mot observert
bestandsutvikling. Overlevelsen får dermed sin identifikasjon fra bestanden,
ikke fra aldersgruppene.

## Spesifikasjon

Kjøretøy følges i årskohorter. Betinget ettårs overlevelse fra alder a til a+1
følger en Weibull-form:

    S(a) = exp(-(a / lambda) ** k)          kumulativ overlevelse til alder a
    s(a) = S(a + 1) / S(a)                  betinget ettårs overlevelse

Weibull er valgt fordi den er standard i litteraturen om bilparkers levetid, har
to tolkbare parametre — skala som levetidsnivå, form som hvor brått avgangen
inntreffer — og fordi en fagfellevurdert kohortmodell for nettopp den norske
bilparken bruker samme familie (Fridstrøm & Østli, ERTRR 2016; står som delvis
verifisert i kilderegisteret).

## To konstruerte ledd, begge eksplisitte

Bruktimport føres inn ved en antatt alder. Kilden oppgir antall
bruktimporterte, men ikke hvor gamle de er. Alderen er en parameter i
antakelsesregisteret, ikke et skjult valg.

Restbestand ved modellstart. Tilgangshistorikken starter i 1995, så en bil som
var 20 år i 2008 er ikke med. Differansen mot observert bestand i startåret
legges inn som en egen, aldrende restpost. Den dør ut med samme kurve som resten
og er null etter få tiår, men den er synlig i utdataene så lenge den finnes.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .datasets import read_extract

MAX_AGE = 40

STOCK_VARIABLE = {"personbiler": "Personbil1", "varebiler": "Varebil4"}
INFLOW_VARIABLE = {"personbiler": "Personbiler", "varebiler": "VareCampBiler"}

# Grov drivlinjedeling — den eneste som er konsistent i tilgangskilden helt
# tilbake til 1995 (jf. D-0022).
DRIVELINES = {
    "elektrisitet": {"tilgang": ["19"], "bestand": ["5"]},
    "ikke_elektrisk": {"tilgang": ["20", "21", "6"], "bestand": ["1", "2", "3", "4", "6"]},
}


@dataclass(frozen=True)
class SurvivalParams:
    """Weibull-parametre for betinget ettårs overlevelse."""
    scale: float          # lambda — levetidsnivå i år
    shape: float          # k — hvor brått avgangen inntreffer
    import_age: int = 3   # antatt alder på bruktimporterte kjøretøy

    def conditional(self, ages: np.ndarray) -> np.ndarray:
        """s(a) = S(a+1)/S(a) for hver alder i `ages`."""
        with np.errstate(divide="ignore", invalid="ignore"):
            s_a = np.exp(-((ages / self.scale) ** self.shape))
            s_neste = np.exp(-(((ages + 1) / self.scale) ** self.shape))
            ut = np.where(s_a > 0, s_neste / s_a, 0.0)
        return np.clip(ut, 0.0, 1.0)


def load_flows(gruppe: str) -> dict[str, pd.DataFrame]:
    """Nye og bruktimporterte per drivlinje og år, samt observert bestand."""
    fr = read_extract("firstreg_14020").copy()
    fr = fr[fr["ContentsCode"] == INFLOW_VARIABLE[gruppe]]
    fr["aar"] = fr["Tid"].astype(str).str[:4]
    hele = fr.groupby("aar")["Tid"].nunique().pipe(lambda s: s[s == 12].index)
    fr = fr[fr["aar"].isin(hele)]

    st = read_extract("stock_07849")
    st = st[st["ContentsCode"] == STOCK_VARIABLE[gruppe]]

    nye, brukt, bestand = {}, {}, {}
    for drivlinje, koder in DRIVELINES.items():
        d = fr[fr["DrivstoffType"].isin(koder["tilgang"])]
        nye[drivlinje] = d[d["TypeRegistrering"] == "N"].groupby("aar")["value"].sum()
        brukt[drivlinje] = d[d["TypeRegistrering"] == "B"].groupby("aar")["value"].sum()
        bestand[drivlinje] = (st[st["DrivstoffType"].isin(koder["bestand"])]
                              .groupby("Tid")["value"].sum())
    return {"nye": pd.DataFrame(nye).sort_index(),
            "brukt": pd.DataFrame(brukt).sort_index(),
            "bestand": pd.DataFrame(bestand).sort_index()}


def simulate(flows: dict[str, pd.DataFrame], params: SurvivalParams, drivlinje: str,
             start_year: str, end_year: str) -> pd.DataFrame:
    """Rull årskohorter fra første tilgangsår til `end_year`.

    Returnerer én rad per år med modellert bestand, restbestanden fra før
    tilgangshistorikken, og gjennomsnittsalder.
    """
    nye, brukt, bestand = flows["nye"], flows["brukt"], flows["bestand"]
    aar_liste = [a for a in nye.index if int(a) <= int(end_year)]
    ages = np.arange(MAX_AGE + 1)
    s = params.conditional(ages)

    kohorter = np.zeros(MAX_AGE + 1)
    rest = 0.0
    rows = []
    for aar in aar_liste:
        # aldring
        kohorter[1:] = kohorter[:-1] * s[:-1]
        kohorter[0] = 0.0
        rest *= s[min(MAX_AGE, 20)]  # restbestanden er gammel; bruk høy alders rate
        # tilgang
        kohorter[0] = nye.loc[aar, drivlinje] if aar in nye.index else 0.0
        if aar in brukt.index:
            kohorter[params.import_age] += brukt.loc[aar, drivlinje]
        # restbestand settes i startåret slik at nivået stemmer med observasjonen
        if aar == start_year and drivlinje in bestand.columns and aar in bestand.index:
            gap = bestand.loc[aar, drivlinje] - kohorter.sum()
            rest = max(0.0, gap)
        modellert = kohorter.sum() + rest
        obs = bestand.loc[aar, drivlinje] if (aar in bestand.index
                                              and drivlinje in bestand.columns) else np.nan
        vekt = kohorter.sum()
        rows.append({
            "drivlinje": drivlinje, "periode": aar,
            "modellert": modellert, "observert": obs,
            "restbestand": rest,
            "restandel_pct": rest / modellert * 100 if modellert else np.nan,
            "gjsn_alder": float((ages * kohorter).sum() / vekt) if vekt else np.nan,
        })
    return pd.DataFrame(rows)


def _sse(flows: dict, params: SurvivalParams, drivlinje: str,
         start_year: str, fit_years: list[str]) -> float:
    sim = simulate(flows, params, drivlinje, start_year, max(fit_years))
    d = sim[sim["periode"].isin(fit_years)].dropna(subset=["observert"])
    if d.empty:
        return float("inf")
    rel = (d["modellert"] - d["observert"]) / d["observert"]
    return float((rel ** 2).sum())


def fit_survival(gruppe: str, drivlinje: str, start_year: str, fit_years: list[str],
                 import_age: int = 3,
                 flows: dict[str, pd.DataFrame] | None = None
                 ) -> tuple[SurvivalParams, float]:
    """Estimer Weibull-parametrene mot observert bestand i `fit_years`.

    Rutenettsøk med etterfølgende forfining. Enkelt og gjennomsiktig framfor en
    optimeringsrutine som skjuler hvor følsom løsningen er. Resultatet rundes til
    søkets egen oppløsning (0,1), slik at utdataene ikke gir inntrykk av en
    presisjon rutenettet ikke har.
    """
    if flows is None:
        flows = load_flows(gruppe)
    beste, beste_sse = None, float("inf")
    for scale in np.arange(8.0, 30.1, 1.0):
        for shape in np.arange(1.5, 8.1, 0.5):
            p = SurvivalParams(scale=round(float(scale), 1), shape=round(float(shape), 1),
                               import_age=import_age)
            v = _sse(flows, p, drivlinje, start_year, fit_years)
            if v < beste_sse:
                beste, beste_sse = p, v
    for scale in np.arange(max(1.0, beste.scale - 1.0), beste.scale + 1.05, 0.1):
        for shape in np.arange(max(0.5, beste.shape - 0.5), beste.shape + 0.55, 0.1):
            p = SurvivalParams(scale=round(float(scale), 1), shape=round(float(shape), 1),
                               import_age=import_age)
            v = _sse(flows, p, drivlinje, start_year, fit_years)
            if v < beste_sse:
                beste, beste_sse = p, v
    return beste, beste_sse


def backcast(gruppe: str, drivlinje: str, start_year: str,
             fit_years: list[str], test_years: list[str],
             import_age: int = 3) -> pd.DataFrame:
    """Estimer på `fit_years`, mål avvik på `test_years` som ikke inngikk."""
    overlapp = set(fit_years) & set(test_years)
    if overlapp:
        raise ValueError(f"estimerings- og testår overlapper: {sorted(overlapp)}")
    if max(fit_years) >= min(test_years):
        raise ValueError("testårene må ligge etter estimeringsårene")
    params, sse = fit_survival(gruppe, drivlinje, start_year, fit_years, import_age)
    flows = load_flows(gruppe)
    sim = simulate(flows, params, drivlinje, start_year, max(test_years))
    d = sim[sim["periode"].isin(test_years)].dropna(subset=["observert"]).copy()
    d["gruppe"] = gruppe
    d["avvik_pct"] = (d["modellert"] - d["observert"]) / d["observert"] * 100
    d["weibull_scale"] = params.scale
    d["weibull_shape"] = params.shape
    d["import_age"] = params.import_age
    d["estimert_paa"] = ",".join(fit_years)
    d["sse_estimering"] = sse
    return d


# Parametre estimert på 2009-2015 og validert på 2016-2025 (D-0027). Låst som
# konstanter slik at artefakter og tester ikke kjører rutenettsøket på nytt;
# `fit_survival` reproduserer dem.
FITTED_PARAMS: dict[str, SurvivalParams] = {
    "ikke_elektrisk": SurvivalParams(scale=20.2, shape=2.4),
    "elektrisitet": SurvivalParams(scale=11.8, shape=4.4),
}

# Rullerende estimeringsvinduer for robusthetsprøven. Sju år hver, forskjøvet tre
# om gangen, slik at det første er valideringens eget og det siste dekker de
# årene valideringen måler mot.
STABILITY_WINDOWS: dict[str, list[str]] = {
    "2009-2015": [str(a) for a in range(2009, 2016)],
    "2012-2018": [str(a) for a in range(2012, 2019)],
    "2016-2022": [str(a) for a in range(2016, 2023)],
    "2019-2025": [str(a) for a in range(2019, 2026)],
}


def _profile_span(flows: dict, drivlinje: str, start_year: str, fit_years: list[str],
                  beste: SurvivalParams, sse_min: float, faktor: float = 2.0
                  ) -> tuple[float, float]:
    """Skalaverdier der SSE holder seg under `faktor` ganger minimum, form fast.

    Dette er en profil over tilpasningen i estimeringsårene, ikke et
    konfidensintervall: residualene er sterkt seriekorrelerte, og profilen sier
    bare hvor skarpt nivået er pinnet av bestandsnivåene i vinduet.
    """
    treff = [round(float(s), 1) for s in np.arange(4.0, 40.01, 0.1)
             if _sse(flows, SurvivalParams(round(float(s), 1), beste.shape, beste.import_age),
                     drivlinje, start_year, fit_years) <= faktor * sse_min]
    return (min(treff), max(treff)) if treff else (float("nan"), float("nan"))


def parameter_stability(gruppe: str = "personbiler", start_year: str = "2008",
                        windows: dict[str, list[str]] | None = None) -> pd.DataFrame:
    """Reestimer parametrene på rullerende vinduer og mål hvor mye de flytter seg.

    Spredningen over vinduene er prosjektets usikkerhetsspenn for
    overlevelsesparametrene. SSE-profilen innenfor ett vindu er langt smalere, og
    tabellen viser begge nettopp for at den smale ikke skal forveksles med
    usikkerhet.
    """
    flows = load_flows(gruppe)
    rows = []
    for drivlinje in DRIVELINES:
        for navn, aar in (windows or STABILITY_WINDOWS).items():
            p, sse = fit_survival(gruppe, drivlinje, start_year, aar, flows=flows)
            lav, hoy = _profile_span(flows, drivlinje, start_year, aar, p, sse)
            rows.append({
                "kontroll": "parameterstabilitet_overlevelse", "gruppe": gruppe,
                "drivlinje": drivlinje, "estimeringsvindu": navn,
                "weibull_scale": p.scale, "weibull_shape": p.shape,
                "import_age": p.import_age, "sse": sse,
                "profil_skala_lav": lav, "profil_skala_hoy": hoy,
            })
    df = pd.DataFrame(rows)
    spenn = df.groupby("drivlinje").agg(
        skala_min=("weibull_scale", "min"), skala_maks=("weibull_scale", "max"),
        form_min=("weibull_shape", "min"), form_maks=("weibull_shape", "max"))
    df = df.merge(spenn, on="drivlinje", how="left")
    df["merknad"] = (
        "spennet over vinduene er registerets usikkerhetsspenn; SSE-profilen "
        "innenfor ett vindu er langt smalere og skal ikke leses som usikkerhet"
    )
    return df
