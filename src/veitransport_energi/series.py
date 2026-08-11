"""Publiserbare historiske serier — fase 2s hovedartefakt.

Alle serier legges i ett langt, maskinlesbart format der hver rad bærer sin egen
status og kilde. Prosjektets begrepsdisiplin krever at leseren alltid kan se om
et tall er observert, konstruert fra observerte data, eller estimert; det løses
her ved at statusen står på raden, ikke i en fotnote.

Statusverdier som brukes i dette laget:
    observert     — tallet står slik i kilden
    konstruert    — aggregat eller skjøt av observerte tall, ingen antakelser
                    utover de dokumenterte skjøtereglene
    estimert      — beregnet med en parameter utenfor kilden (energifaktorer)

Framtidsrettede statuser (scenarioforutsatt) hører til fase 5 og forekommer
ikke her.
"""
from __future__ import annotations

import pandas as pd

from .datasets import read_extract
from .energy import MJ_PER_LITER
from .energy import SOURCE as ENERGY_SOURCE
from .splice import autodiesel_segments, bensin_series, dieselsum_series

COLUMNS = [
    "serie_id", "gruppe", "drivlinje", "variabel", "enhet",
    "frekvens", "periode", "verdi", "status", "kilde", "segment", "brudd",
]

# Kjøretøygrupper i modellen, med kildekoblingene koblingskontrollen bekreftet (D-0020).
GROUPS: dict[str, dict[str, object]] = {
    "personbiler": {"km_koder": ["20"], "bestand": "Personbil1"},
    "varebiler": {"km_koder": ["29", "30"], "bestand": "Varebil4"},
}

# Drivlinjer som publiseres hver for seg. Øvrige koder samles i «annet» for at
# gruppesummen skal stemme uten at små, ustabile kategorier gis falsk presisjon.
DRIVLINJER: dict[str, list[str]] = {
    "bensin": ["1"],
    "diesel": ["2"],
    "elektrisitet": ["18"],
    "hybrid_ladbar": ["14", "16"],
    "hybrid_ikke_ladbar": ["15", "17"],
    "annet": ["3", "4", "13", "7"],
}

MJ_PER_KWH = 3.6


def _row(**kw) -> dict:
    r = {c: "" for c in COLUMNS}
    r.update(kw)
    return r


def sales_series() -> list[dict]:
    """Månedlige salgsserier, segmentert etter skjøtereglene (D-0002, D-0003)."""
    s03, s11, s13 = (read_extract(n) for n in ("sales_03687", "sales_11174", "sales_13585"))
    rows: list[dict] = []

    for df, serie_id, drivlinje in (
        (bensin_series(s03, s11, s13), "salg_bilbensin", "bensin"),
        (dieselsum_series(s03, s11), "salg_dieselsum", "diesel"),
        (autodiesel_segments(s11, s13), "salg_autodiesel", "diesel"),
    ):
        for _, r in df.iterrows():
            brudd = ""
            if serie_id == "salg_autodiesel" and r["Tid"] == "2020M01":
                brudd = "innsamlingskorreksjon 2020: ikke sammenlignbar med tidligere perioder"
            rows.append(_row(
                serie_id=serie_id, gruppe="veitransport_og_ovrig", drivlinje=drivlinje,
                variabel="salgsvolum", enhet="mill. liter", frekvens="M",
                periode=r["Tid"], verdi=r["value"], status="konstruert",
                kilde="SSB 03687/11174/13585 (petroleumsmåltallet)", segment=r["segment"], brudd=brudd,
            ))
    return rows


def stock_series() -> list[dict]:
    """Kjøretøybestand per 31.12 og drivstofftype (07849)."""
    st = read_extract("stock_07849")
    navn = {"1": "bensin", "2": "diesel", "5": "elektrisitet", "3": "annet", "4": "annet",
            "6": "hybrid_og_annet"}
    rows: list[dict] = []
    for gruppe, spec in GROUPS.items():
        d = st[st["ContentsCode"] == spec["bestand"]]
        for (tid, kode), v in d.groupby(["Tid", "DrivstoffType"])["value"].sum().items():
            rows.append(_row(
                serie_id="bestand", gruppe=gruppe, drivlinje=navn.get(kode, "annet"),
                variabel="bestand_3112", enhet="kjøretøy", frekvens="A",
                periode=tid, verdi=v, status="observert", kilde="SSB 07849",
                brudd=("hybrider kan ikke skilles ut; ligger i «annet drivstoff»"
                       if kode == "6" else ""),
            ))
    return rows


def mileage_series() -> list[dict]:
    """Kjørelengder per drivlinje (12577), aggregert til modellens kjøretøygrupper.

    Serien inneholder en eksplisitt restpost «uspesifisert». SSB undertrykker små
    kategorier, slik at summen av drivlinjene ligger under kildens totalserie —
    inntil 0,6 prosent for varebiler i de tidligste årene. Differansen publiseres
    som egen linje framfor å forsvinne, slik at gruppesummen stemmer eksakt og
    leseren ser hvor mye som ikke lar seg fordele.
    """
    km = read_extract("km_12577")
    tot = km[km["ContentsCode"] == "Kjorelengde"]
    publiserte = [k for koder in DRIVLINJER.values() for k in koder]
    rows: list[dict] = []
    for gruppe, spec in GROUPS.items():
        d = tot[tot["Kjoretoytype"].isin(spec["km_koder"])]
        kildens_total = d[d["DrivstoffType"] == "0"].groupby("Tid")["value"].sum()
        sum_deler = d[d["DrivstoffType"].isin(publiserte)].groupby("Tid")["value"].sum()
        for tid, total in kildens_total.items():
            rest = total - sum_deler.get(tid, 0.0)
            rows.append(_row(
                serie_id="kjorelengde", gruppe=gruppe, drivlinje="uspesifisert",
                variabel="kjorelengde_total", enhet="mill. km", frekvens="A",
                periode=tid, verdi=rest, status="konstruert", kilde="SSB 12577",
                segment="+".join(spec["km_koder"]),
                brudd="restpost: kategorier undertrykt av SSB, ikke fordelbare på drivlinje",
            ))
        for drivlinje, koder in DRIVLINJER.items():
            s = d[d["DrivstoffType"].isin(koder)].groupby("Tid")["value"].sum()
            for tid, v in s.items():
                brudd = ""
                if int(tid) <= 2015 and drivlinje.startswith("hybrid"):
                    brudd = "hybrider registrert som bensin/diesel til og med 2015"
                elif tid == "2020":
                    brudd = "nytt kjøretøyregister mars 2020; avvik på detaljnivå mot 2019"
                rows.append(_row(
                    serie_id="kjorelengde", gruppe=gruppe, drivlinje=drivlinje,
                    variabel="kjorelengde_total", enhet="mill. km", frekvens="A",
                    periode=tid, verdi=v,
                    status="observert" if len(koder) == 1 else "konstruert",
                    kilde="SSB 12577", segment="+".join(spec["km_koder"]), brudd=brudd,
                ))
    return rows


def energy_series() -> list[dict]:
    """Energibruk fra flytende drivstoff, beregnet fra observert salgsvolum.

    Bevisst avgrensning: dette laget omregner SALGSVOLUM til energi med de
    verifiserte NCV-faktorene (D-0018). Energibruk per kjøretøygruppe krever
    intensiteter som ennå ikke er kalibrert, og hører til fase 3 — å publisere
    den her ville vært å presentere en modellstørrelse som statistikk.
    """
    s11, s13 = read_extract("sales_11174"), read_extract("sales_13585")
    rows: list[dict] = []

    def add(df: pd.DataFrame, produkt: str, drivlinje: str, faktor_navn: str, kilde: str):
        aar = df.copy()
        aar["aar"] = aar["Tid"].astype(str).str[:4]
        hele = aar.groupby("aar")["Tid"].nunique().pipe(lambda s: s[s == 12].index)
        s = aar[aar["aar"].isin(hele)].groupby("aar")["value"].sum()
        for tid, mill_liter in s.items():
            gwh = mill_liter * 1e6 * MJ_PER_LITER[faktor_navn] / MJ_PER_KWH / 1e6
            rows.append(_row(
                serie_id=f"energi_{produkt}", gruppe="veitransport_og_ovrig", drivlinje=drivlinje,
                variabel="energi_salgsvolum", enhet="GWh", frekvens="A",
                periode=tid, verdi=gwh, status="estimert", kilde=kilde,
                brudd=("fossil NCV brukt på hele volumet; iblandet bio har lavere "
                       "brennverdi, så tallet er en svak overkant"),
            ))

    p11 = s11[s11["PetroleumProd"] == "03"]
    p13 = s13[(s13["ContentsCode"] == "Petroleum") & (s13["Produkter"] == "01")]
    add(p11[p11["Tid"] < "2021M01"], "bilbensin", "bensin", "bensin", f"SSB 11174 × {ENERGY_SOURCE}")
    add(p13, "bilbensin", "bensin", "bensin", f"SSB 13585 × {ENERGY_SOURCE}")

    a11 = s11[s11["PetroleumProd"] == "04b"]
    a13 = s13[(s13["ContentsCode"] == "Petroleum") & (s13["Produkter"] == "02a")]
    add(a11[a11["Tid"] < "2021M01"], "autodiesel", "diesel", "autodiesel_fossil",
        f"SSB 11174 × {ENERGY_SOURCE}")
    add(a13, "autodiesel", "diesel", "autodiesel_fossil", f"SSB 13585 × {ENERGY_SOURCE}")
    return rows


def build_historical_statistics() -> pd.DataFrame:
    rows = sales_series() + stock_series() + mileage_series() + energy_series()
    df = pd.DataFrame(rows, columns=COLUMNS)
    return df.sort_values(["serie_id", "gruppe", "drivlinje", "periode"]).reset_index(drop=True)
