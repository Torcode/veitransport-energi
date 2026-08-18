"""Koblingskontroll mellom kjøretøygruppene i de tre registerkildene.

Designporten (D-0004) satte varebiler som sekundærmodul «etter koblingskontroll»,
fordi kategoriene ikke er identisk avgrenset i bestand (07849), kjørelengder
(12577) og førstegangsregistreringer (14020/12906). Denne modulen gjør den
kontrollen etterprøvbar.

Tre spørsmål besvares:

1. Er aggregatene i kjørelengdetabellen interne summer av underkategoriene?
   (Ellers kan aggregatene ikke brukes til å bygge kjøretøygrupper.)
2. Hvor godt svarer implisitt antall kjøretøy i bruk (kjørelengde delt på
   gjennomsnittlig kjørelengde) til registrert bestand per 31.12?
3. Hva koster det å bruke 14020 framfor 12906 som tilgangsledd?

Merk om nivåforskjellen i punkt 2: 12577 dekker kjøretøy som var registrert i
løpet av året, 07849 teller beholdningen ved utgangen. Et positivt avvik er
derfor forventet og skal ikke tolkes som feil i noen av kildene — det er
størrelsen og stabiliteten som avgjør om koblingen er brukbar.
"""
from __future__ import annotations

import pandas as pd

from .datasets import read_extract

# Kjørelengdetabellens aggregater og de underkategoriene de skal være summen av.
KM_AGGREGATES: dict[str, list[str]] = {
    "15": ["20", "21", "22", "23"],          # Personbiler i alt
    "16": ["24", "25"],                      # Busser i alt
    "00": ["26", "27", "28", "29", "30"],    # Små godsbiler i alt
    "17": ["31", "32", "33"],                # Store lastebiler i alt
    "0": ["15", "16", "00", "17"],           # Kjøretøy i alt
}

# Kandidatkoblinger: bestandsvariabel i 07849 -> kjøretøytyper i 12577.
LINKAGE_CANDIDATES: dict[str, dict[str, list[str]]] = {
    "Personbil1": {
        "kun personbiler (20)": ["20"],
        "personbiler + drosjer (20+21)": ["20", "21"],
        "personbiler i alt (15)": ["15"],
    },
    "Varebil4": {
        "små + store varebiler (29+30)": ["29", "30"],
        "små godsbiler i alt (00)": ["00"],
    },
}


def _km_pivots() -> tuple[pd.DataFrame, pd.DataFrame]:
    km = read_extract("km_12577")
    k = km[km["DrivstoffType"] == "0"]          # alle typer drivstoff
    tot = k[k["ContentsCode"] == "Kjorelengde"].pivot_table(
        index="Tid", columns="Kjoretoytype", values="value", aggfunc="sum")
    avg = k[k["ContentsCode"] == "GjsnittKjorelengde"].pivot_table(
        index="Tid", columns="Kjoretoytype", values="value", aggfunc="sum")
    return tot, avg


def aggregate_identities() -> pd.DataFrame:
    """Avvik mellom hvert aggregat og summen av underkategoriene, per år (prosent)."""
    tot, _ = _km_pivots()
    rows = []
    for agg, parts in KM_AGGREGATES.items():
        for tid in tot.index:
            a = tot.loc[tid, agg]
            s = tot.loc[tid, parts].sum()
            rows.append({"Tid": tid, "aggregat": agg, "deler": "+".join(parts),
                         "aggregat_verdi": a, "sum_deler": s,
                         "avvik_pct": (s - a) / a * 100 if a else float("nan")})
    return pd.DataFrame(rows)


def implied_vehicles() -> pd.DataFrame:
    """Implisitt antall kjøretøy i bruk per kjøretøytype og år (12577)."""
    tot, avg = _km_pivots()
    return tot * 1e6 / avg


def stock_vs_activity() -> pd.DataFrame:
    """Implisitt antall (12577) mot registrert bestand (07849) for hver kandidatkobling."""
    impl = implied_vehicles()
    st = read_extract("stock_07849")
    stock = st.pivot_table(index="Tid", columns="ContentsCode", values="value", aggfunc="sum")
    rows = []
    for var, kandidater in LINKAGE_CANDIDATES.items():
        for navn, koder in kandidater.items():
            for tid in stock.index:
                if tid not in impl.index:
                    continue
                b = stock.loc[tid, var]
                a = impl.loc[tid, koder].sum()
                rows.append({"Tid": tid, "bestandsvariabel": var, "kobling": navn,
                             "bestand_3112": b, "implisitt_i_bruk": a,
                             "avvik_pct": (a / b - 1) * 100 if b else float("nan")})
    return pd.DataFrame(rows)


def inflow_source_comparison() -> pd.DataFrame:
    """14020 mot 12906 som tilgangsledd, med bobilandelen 14020 ikke kan skille ut."""
    f9 = read_extract("firstreg_12906")
    f0 = read_extract("firstreg_14020").copy()
    f0["aar"] = f0["Tid"].astype(str).str[:4]
    a9 = f9.groupby(["Tid", "ContentsCode"])["value"].sum().unstack()
    a0 = f0.groupby(["aar", "ContentsCode"])["value"].sum().unstack()
    rows = []
    for tid in a9.index:
        if tid not in a0.index:
            continue
        pb0, pb9 = a0.loc[tid, "Personbiler"], a9.loc[tid, "Personbil1"]
        vc0 = a0.loc[tid, "VareCampBiler"]
        vb, bo = a9.loc[tid, "Varebil4"], a9.loc[tid, "Bobiler"]
        rows.append({
            "Tid": tid,
            "personbiler_14020": pb0, "personbiler_12906": pb9,
            "personbiler_avvik_pct": (pb9 / pb0 - 1) * 100,
            "varecamp_14020": vc0, "vare_pluss_bobil_12906": vb + bo,
            "varecamp_avvik_pct": ((vb + bo) / vc0 - 1) * 100,
            "bobilandel_pct": bo / (vb + bo) * 100,
        })
    return pd.DataFrame(rows)


# De to registreringstabellene bruker hvert sitt kodeverk for drivstoff. 14020 har
# fire aggregerte kategorier, 12906 har SSBs detaljerte klassifikasjon. Kartet under
# er den mest velvillige oversettelsen mellom dem — og kontrollen under viser at den
# likevel ikke gir samme tall.
INFLOW_CATEGORY_MAP: dict[str, dict[str, list[str]]] = {
    "nullutslipp": {"14020": ["19"], "12906": ["5", "13"]},
    "fossil": {"14020": ["20"], "12906": ["1", "2"]},
    "hybrid": {"14020": ["21"], "12906": ["14", "15", "16", "17"]},
    "annet": {"14020": ["6"], "12906": ["3", "4", "6"]},
}

# Kjøretøygrupper: 14020 kan ikke skille bobiler fra varebiler, så vare-gruppen
# sammenlignes mot summen Varebil4 + Bobiler i 12906.
INFLOW_GROUP_MAP: dict[str, dict[str, list[str]]] = {
    "personbiler": {"14020": ["Personbiler"], "12906": ["Personbil1"]},
    "vare_og_camping": {"14020": ["VareCampBiler"], "12906": ["Varebil4", "Bobiler"]},
}

INFLOW_SOURCE_NOTE = (
    "de to førstegangsregistreringstabellene beskriver samme populasjon, men med hvert "
    "sitt drivstoffkodeverk: 14020 har fire aggregerte kategorier, 12906 har SSBs "
    "detaljerte klassifikasjon — den samme som bestandstabellen 07849 bruker. Et "
    "forholdstall mellom tilgang og bestand skal derfor bygges på 12906 (D-0036). "
    "To ulike avvik ligger i tabellen. Det ene er systematisk: fossilkategorien skiller "
    "seg med 67–133 kjøretøy hvert år fra 2020, et nesten konstant antall, mens den "
    "relative forskjellen vokser fra 0,5 til 2,8 prosent fordi den fossile tilgangen "
    "kollapser under den. Det andre gjelder totalen og opptrer bare i randårene 2019 og "
    "2025 (1,2 og 1,4 prosent); mekanismen bak det er ikke identifisert fra det som er "
    "hentet, og noteres framfor å bli glattet"
)


def inflow_source_by_drivetrain() -> pd.DataFrame:
    """14020 mot 12906, i alt og per drivlinjeaggregat.

    `inflow_source_comparison` viser at totalene nesten stemmer. Denne viser hvor
    de ikke gjør det, og er grunnen til at valget av tilgangskilde ikke er
    likegyldig: i 2025 fører 14020 flere kjøretøy som fossile og færre som
    nullutslipp enn den detaljerte klassifikasjonen gjør. Forskjellen er liten i
    prosent av totalen og stor i prosent av den fossile tilgangen, som er nettopp
    den størrelsen forsidens hovedfunn hviler på.
    """
    f0 = read_extract("firstreg_14020").copy()
    f0["aar"] = f0["Tid"].astype(str).str[:4]
    hele = f0.groupby("aar")["Tid"].nunique().pipe(lambda x: x[x == 12].index)
    f0 = f0[f0["aar"].isin(hele)]
    f9 = read_extract("firstreg_12906").copy()
    f9["aar"] = f9["Tid"].astype(str)

    def sum_av(d: pd.DataFrame, grupper: list[str], koder: list[str] | None) -> pd.Series:
        u = d[d["ContentsCode"].isin(grupper)]
        if koder is not None:
            u = u[u["DrivstoffType"].isin(koder)]
        return u.groupby("aar")["value"].sum()

    rader = []
    aar_felles = sorted(set(f0["aar"]) & set(f9["aar"]))
    for gruppe, gk in INFLOW_GROUP_MAP.items():
        kategorier = {"i_alt": {"14020": None, "12906": None}, **INFLOW_CATEGORY_MAP}
        for kategori, kk in kategorier.items():
            a0 = sum_av(f0, gk["14020"], kk["14020"])
            a9 = sum_av(f9, gk["12906"], kk["12906"])
            for aar in aar_felles:
                v0, v9 = float(a0.get(aar, 0.0)), float(a9.get(aar, 0.0))
                rader.append({
                    "kontroll": "tilgangskilde_14020_mot_12906",
                    "gruppe": gruppe,
                    "kategori": kategori,
                    "periode": aar,
                    "antall_14020": int(round(v0)),
                    "antall_12906": int(round(v9)),
                    "avvik_antall": int(round(v9 - v0)),
                    "avvik_pct": (v9 / v0 - 1) * 100 if v0 else float("nan"),
                    "merknad": INFLOW_SOURCE_NOTE,
                })
    return pd.DataFrame(rader)
