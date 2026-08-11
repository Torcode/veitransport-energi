"""Historisk rekonstruksjon: nettoavgang og kalibrerte energiintensiteter.

Andre halvdel av fase 2. Der `series.py` publiserer det som er observert eller
enkelt konstruert, rekonstruerer denne modulen to størrelser som ikke kan leses
direkte ut av noen kilde, men som modellen i fase 3 hviler på.

## Nettoavgang

Følger av bestandsidentiteten

    bestand[f, t] = bestand[f, t-1] + tilgang[f, t] - nettoavgang[f, t]

og beregnes som residual. Den skal aldri omtales som vraking (D-0007): den
inneholder også eksport, avregistrering og omklassifisering mellom
drivstoffkoder.

Residualen beregnes bare der tilgangs- og bestandskategoriene faktisk svarer til
hverandre. Fram til og med 2015 registrerte bestandstabellen hybrider som
ordinære bensin- og dieselbiler, mens registreringstabellen førte dem som
hybrider. En residual for «fossil» og «hybrid» hver for seg blir da meningsløs —
i 2015 gir den en avgangsrate på over 1 800 prosent, som er ren
kategoriforflytning. Derfor publiseres `elektrisitet` og `ikke_elektrisk` for
hele perioden, mens `fossil_samlet` og `hybrid_og_annet` bare beregnes fra og med
2017, når begge kildene fører hybrider i egen kategori.

## Energiintensitet

Kalibreres som energibalansens produktpost delt på observert kjørelengde for
samme energibærer. Begge ledd er uavhengig målt — energibalansen fra
leveransestatistikk, kjørelengdene fra odometeravlesninger.

Nevneren krever et valg som endrer konklusjonen fullstendig. Kjørelengdetabellen
skiller fra 2016 ut hybridenes kilometer i egne koder, mens energibalansens
bensinpost fortsatt inneholder alt bensinen de bruker. Regnes intensiteten mot
bensinkoden alene, framstår bensinflåten som 29 prosent *mindre* effektiv fra
2010 til 2024. Tas hybridenes bensinkilometer med, går utviklingen motsatt vei.
Sannheten avhenger av hvor stor del av de ladbare hybridenes kjøring som skjer på
forbrenningsmotor — utility factor — og den parameteren har ennå ingen verifisert
norsk kilde i dette prosjektet.

Funksjonen krever derfor at valget gjøres eksplisitt: enten oppgis en utility
factor, eller så returneres begge grensene (0 og 1) slik at leseren ser spennet.
Ikke-ladbare hybrider henter all energi fra drivstoff og regnes alltid med.
"""
from __future__ import annotations

import pandas as pd

from .datasets import read_extract
from .diagnostics import EB_ELECTRICITY_CODE, EB_FOSSIL_CODES
from .energy import MJ_PER_LITER

MJ_PER_KWH = 3.6

STOCK_VARIABLE = {"personbiler": "Personbil1", "varebiler": "Varebil4"}
INFLOW_VARIABLE = {"personbiler": "Personbiler", "varebiler": "VareCampBiler"}

# Året fra og med hvilket bestandstabellen fører hybrider i egen kategori.
HYBRID_SPLIT_YEAR = 2017

RETIREMENT_GROUPS: dict[str, dict] = {
    "elektrisitet": {"tilgang": ["19"], "bestand": ["5"], "fra_aar": None},
    "ikke_elektrisk": {"tilgang": ["20", "21", "6"], "bestand": ["1", "2", "3", "4", "6"],
                       "fra_aar": None},
    "fossil_samlet": {"tilgang": ["20"], "bestand": ["1", "2"], "fra_aar": HYBRID_SPLIT_YEAR},
    "hybrid_og_annet": {"tilgang": ["21", "6"], "bestand": ["3", "4", "6"],
                        "fra_aar": HYBRID_SPLIT_YEAR},
}

# Kalibreringsgrunnlag. `km_alltid` er kjørelengdekoder som utvilsomt hører til
# energibæreren; `km_ladbar` er ladbare hybrider, der bare en andel av kjøringen
# skjer på denne bæreren.
#
# `ladbar_vekt` sier hvordan utility factor slår inn for den enkelte bæreren.
# For drivstoff er andelen av de ladbare hybridenes kjøring lik UF; for
# elektrisitet er den komplementet, siden kilometrene deres fordeles mellom de to
# energibærerne og ikke kan telle fullt i begge.
INTENSITY_BASIS: dict[str, dict] = {
    "bensin": {"eb_kode": EB_FOSSIL_CODES[0], "km_alltid": ["1", "15"], "km_ladbar": ["14"],
               "ladbar_vekt": "uf", "faktor": "bensin"},
    "diesel": {"eb_kode": EB_FOSSIL_CODES[1], "km_alltid": ["2", "17"], "km_ladbar": ["16"],
               "ladbar_vekt": "uf", "faktor": "autodiesel_fossil"},
    "elektrisitet": {"eb_kode": EB_ELECTRICITY_CODE, "km_alltid": ["18"],
                     "km_ladbar": ["14", "16"], "ladbar_vekt": "1-uf", "faktor": None},
}


def net_retirement() -> pd.DataFrame:
    """Nettoavgang per kjøretøygruppe, drivlinjegruppe og år (residual)."""
    st = read_extract("stock_07849")
    fr = read_extract("firstreg_14020").copy()
    fr["aar"] = fr["Tid"].astype(str).str[:4]
    hele = fr.groupby("aar")["Tid"].nunique().pipe(lambda s: s[s == 12].index)
    fr = fr[fr["aar"].isin(hele)]

    rows = []
    for gruppe, stock_var in STOCK_VARIABLE.items():
        s = st[st["ContentsCode"] == stock_var]
        f = fr[fr["ContentsCode"] == INFLOW_VARIABLE[gruppe]]
        for drivlinje, kart in RETIREMENT_GROUPS.items():
            bestand = (s[s["DrivstoffType"].isin(kart["bestand"])]
                       .groupby("Tid")["value"].sum().sort_index())
            tilgang = (f[f["DrivstoffType"].isin(kart["tilgang"])]
                       .groupby("aar")["value"].sum().sort_index())
            for aar in bestand.index:
                forrige_aar = str(int(aar) - 1)
                if forrige_aar not in bestand.index or aar not in tilgang.index:
                    continue
                if kart["fra_aar"] and int(aar) < kart["fra_aar"]:
                    continue
                forrige = bestand[forrige_aar]
                netto = forrige + tilgang[aar] - bestand[aar]
                rows.append({
                    "gruppe": gruppe, "drivlinje": drivlinje, "periode": aar,
                    "bestand_forrige": forrige, "tilgang": tilgang[aar],
                    "bestand": bestand[aar], "nettoavgang": netto,
                    "avgangsrate_pct": netto / forrige * 100 if forrige else float("nan"),
                    "status": "konstruert",
                })
    df = pd.DataFrame(rows)
    df["merknad"] = (
        "residual: omfatter vraking, eksport, avregistrering og omklassifisering — "
        "ikke vraking alene (D-0007). Tilgang fra 14020, nye og bruktimporterte"
    )
    df.loc[df["drivlinje"].isin(["fossil_samlet", "hybrid_og_annet"]), "merknad"] += (
        f"; beregnes først fra {HYBRID_SPLIT_YEAR}, da begge kildene fører hybrider "
        "i egen kategori"
    )
    df.loc[df["gruppe"] == "varebiler", "merknad"] += (
        "; tilgangen inkluderer campingbiler, som ikke inngår i bestandsvariabelen"
    )
    return df.sort_values(["gruppe", "drivlinje", "periode"]).reset_index(drop=True)


def calibrated_intensity(utility_factor: float | None = None) -> pd.DataFrame:
    """Flåtegjennomsnittlig energiintensitet per energibærer og år.

    utility_factor: andelen av ladbare hybriders kjørelengde som skal tilskrives
    forbrenningsmotoren (0–1). Utelates den, returneres begge grensene, slik at
    spennet er synlig framfor skjult i et enkelttall. Se modulens dokumentasjon.
    """
    if utility_factor is not None and not 0.0 <= utility_factor <= 1.0:
        raise ValueError("utility_factor må ligge mellom 0 og 1")

    eb = read_extract("energybalance_11561_road").copy()
    eb = eb[eb["ContentsCode"] == "EnergibalansenPJ"]
    eb["aar"] = eb["Tid"].astype(str).str[:4]
    ebp = eb.pivot_table(index="aar", columns="EnergiProdukt", values="value", aggfunc="sum")

    km = read_extract("km_12577")
    k = km[(km["ContentsCode"] == "Kjorelengde") & (km["Kjoretoytype"] == "0")]
    kmp = k.pivot_table(index="Tid", columns="DrivstoffType", values="value", aggfunc="sum")

    def km_sum(aar: str, koder: list[str]) -> float:
        return float(sum(kmp.loc[aar, c] for c in koder
                         if c in kmp.columns and pd.notna(kmp.loc[aar, c])))

    uf_verdier = [utility_factor] if utility_factor is not None else [0.0, 1.0]
    rows = []
    for baerer, spec in INTENSITY_BASIS.items():
        for aar in sorted(set(ebp.index) & set(kmp.index)):
            if spec["eb_kode"] not in ebp.columns or pd.isna(ebp.loc[aar, spec["eb_kode"]]):
                continue
            pj = float(ebp.loc[aar, spec["eb_kode"]])
            fast = km_sum(aar, spec["km_alltid"])
            ladbar = km_sum(aar, spec["km_ladbar"])
            if not fast:
                continue
            for uf in uf_verdier:
                vekt = uf if spec["ladbar_vekt"] == "uf" else 1.0 - uf
                mill_km = fast + vekt * ladbar
                km_abs = mill_km * 1e6
                rad = {
                    "energibaerer": baerer, "periode": aar, "utility_factor": uf,
                    "ladbar_vekt": vekt,
                    "energi_PJ": pj, "kjorelengde_mill_km": mill_km,
                    "ladbar_andel_av_nevner_pct": vekt * ladbar / mill_km * 100 if mill_km else 0.0,
                    "kwh_per_km": pj * 1e9 / MJ_PER_KWH / km_abs,
                    "liter_per_mil": float("nan"),
                    "status": "kalibrert",
                }
                if spec["faktor"]:
                    rad["liter_per_mil"] = pj * 1e9 / MJ_PER_LITER[spec["faktor"]] / km_abs * 10
                rows.append(rad)
    df = pd.DataFrame(rows)
    df["merknad"] = (
        "energibalansens produktpost delt på observert kjørelengde; gjelder hele "
        "veitransporten, ikke én kjøretøygruppe. Fossilpostene er ekskl. innblandet "
        "biodrivstoff. Nevneren avhenger av utility_factor for ladbare hybrider — "
        "uten den er utviklingen over tid ikke tolkbar"
    )
    return df.sort_values(["energibaerer", "periode", "utility_factor"]).reset_index(drop=True)
