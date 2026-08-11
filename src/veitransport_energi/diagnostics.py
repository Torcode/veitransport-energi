"""Avstemming mellom salgsstatistikk og energibalansens veitransportpost.

Dette er prosjektets første reelle kryssystem-kontroll: salgsstatistikken
(rapportert av oljeselskapene, mill. liter) mot energibalansen (SSBs
regnskapsavstemte energipost for veitransport, PJ). Kontrollen ble mulig først
da brennverdifaktorene var verifisert i primærkilden (D-0018).

Viktig om sammenlignbarhet:
- Salgsvolumet i 11174/13585 (petroleumsmåltallet) INKLUDERER iblandet
  biodrivstoff.
- Energibalansens produktposter «Bensin (ekskl. bio)» og «Autodiesel
  (ekskl. bio)» er EKSKLUSIV bio, mens bioandelen ligger i egen post
  «Flytende biobrensler».
Sammenligning per produkt er derfor ikke meningsfull uten å vite hvordan
energibalansen fordeler bioposten mellom bensin og autodiesel. Den
sammenlignbare størrelsen er SUMMEN bensin + autodiesel + flytende
biobrensler mot summen av salgsenergien.
"""
from __future__ import annotations

import pandas as pd

from .energy import MJ_PER_LITER

EB_FOSSIL_LABELS = ("Bensin  (ekskl. bio)", "Autodiesel  (ekskl. bio)")
EB_BIO_LABEL = "Flytende biobrensler"


def _annual_sales_mill_liter(sales_11174: pd.DataFrame, sales_13585: pd.DataFrame) -> pd.DataFrame:
    """Årlig salg av bilbensin og autodiesel (petroleumsmåltallet, mill. liter).

    11174 brukes til og med 2021, 13585 fra 2022 (jf. skjøtereglene, D-0002).
    Bare hele år tas med.
    """
    a11 = sales_11174.copy()
    a11["aar"] = a11["Tid"].astype(str).str[:4].astype(int)
    full11 = a11.groupby("aar")["Tid"].nunique().pipe(lambda s: s[s == 12].index)
    p11 = (a11[a11["aar"].isin(full11)]
           .groupby(["aar", "PetroleumProd"])["value"].sum().unstack())

    a13 = sales_13585[sales_13585["ContentsCode"] == "Petroleum"].copy()
    a13["aar"] = a13["Tid"].astype(str).str[:4].astype(int)
    full13 = a13.groupby("aar")["Tid"].nunique().pipe(lambda s: s[s == 12].index)
    p13 = (a13[a13["aar"].isin(full13)]
           .groupby(["aar", "Produkter"])["value"].sum().unstack())

    rows = []
    for aar in sorted(set(p11.index) | set(p13.index)):
        if aar >= 2022 and aar in p13.index:
            rows.append({"aar": aar, "bensin": float(p13.loc[aar, "01"]),
                         "autodiesel": float(p13.loc[aar, "02a"]), "kilde": "13585"})
        elif aar in p11.index:
            rows.append({"aar": aar, "bensin": float(p11.loc[aar, "03"]),
                         "autodiesel": float(p11.loc[aar, "04b"]), "kilde": "11174"})
    return pd.DataFrame(rows).set_index("aar")


def energy_reconciliation(
    sales_11174: pd.DataFrame,
    sales_13585: pd.DataFrame,
    energybalance_road: pd.DataFrame,
    first_year: int = 2010,
) -> pd.DataFrame:
    """Årlig avstemming av veitransportenergi: energibalanse mot salg.

    Returnerer per år: salgsenergi (PJ, fossile faktorer på hele volumet),
    energibalansens fossilsum, biopost og totalsum, samt forholdstallet
    EB-sum/salgsenergi. Et forholdstall nær 1 betyr at de to systemene
    beskriver samme energimengde.

    Merk at salgsenergien er en OVRE tilnærming: fossile brennverdier brukes på
    hele volumet, mens den iblandede bioandelen faktisk har lavere brennverdi.
    Beregnet forholdstall er derfor svakt konservativt (litt under 1).
    """
    eb = energybalance_road[energybalance_road["ContentsCode"] == "EnergibalansenPJ"].copy()
    # Tid kan være lest som tekst eller tall avhengig av innlesing; normaliser til
    # årstall (int) slik at oppslaget mot salgsårene alltid treffer.
    eb["Tid"] = eb["Tid"].astype(str).str.slice(0, 4).astype(int)
    ebp = eb.pivot_table(index="Tid", columns="EnergiProdukt_label", values="value")
    sales = _annual_sales_mill_liter(sales_11174, sales_13585)

    rows = []
    for aar, r in sales.iterrows():
        if aar < first_year or aar not in ebp.index:
            continue
        fossil = sum(float(ebp.loc[aar, c]) for c in EB_FOSSIL_LABELS if c in ebp.columns
                     and pd.notna(ebp.loc[aar, c]))
        bio = float(ebp.loc[aar, EB_BIO_LABEL]) if (EB_BIO_LABEL in ebp.columns
                                                    and pd.notna(ebp.loc[aar, EB_BIO_LABEL])) else 0.0
        salg_pj = (r["bensin"] * 1e6 * MJ_PER_LITER["bensin"]
                   + r["autodiesel"] * 1e6 * MJ_PER_LITER["autodiesel_fossil"]) / 1e9
        rows.append({
            "aar": int(aar),
            "salg_mill_liter_bensin": r["bensin"],
            "salg_mill_liter_autodiesel": r["autodiesel"],
            "salgskilde": r["kilde"],
            "salgsenergi_PJ": salg_pj,
            "eb_fossil_PJ": fossil,
            "eb_bio_PJ": bio,
            "eb_sum_PJ": fossil + bio,
            "eb_per_salg": (fossil + bio) / salg_pj,
        })
    return pd.DataFrame(rows).set_index("aar")
