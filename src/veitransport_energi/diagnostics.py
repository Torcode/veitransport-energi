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

from .datasets import read_extract
from .energy import MJ_PER_LITER

# Energibalansen identifiseres på KODE, ikke etikett. Produktdimensjonen er
# hierarkisk, og flere nivåer bærer samme etikett: «Elektrisitet» finnes både som
# EP07 og EP070 med identisk verdi, «Alle energiprodukter» som EPTOT00 og EPTOT01,
# og EP04IF er et aggregat over bensin, autodiesel og LPG. Å velge produkter på
# etikett og summere ville dobbelttelle. Kodene under er alle bladnivå.
EB_FOSSIL_CODES = ("EP0465IF", "EP0467112IF")   # bensin og autodiesel, ekskl. bio
EB_BIO_CODE = "EP052"                            # flytende biobrensler (ikke biogass, EP053)
EB_ELECTRICITY_CODE = "EP070"                    # elektrisitet, bladnivå


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
    ebp = eb.pivot_table(index="Tid", columns="EnergiProdukt", values="value", aggfunc="sum")
    sales = _annual_sales_mill_liter(sales_11174, sales_13585)

    def _pj(aar: int, kode: str) -> float:
        if kode not in ebp.columns or pd.isna(ebp.loc[aar, kode]):
            return 0.0
        return float(ebp.loc[aar, kode])

    rows = []
    for aar, r in sales.iterrows():
        if aar < first_year or aar not in ebp.index:
            continue
        fossil = sum(_pj(aar, kode) for kode in EB_FOSSIL_CODES)
        bio = _pj(aar, EB_BIO_CODE)
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


def utility_factor_identification(
    bev_intensity_range: tuple[float, ...] = (0.18, 0.20, 0.22, 0.24),
) -> pd.DataFrame:
    """Kan utility factor bestemmes fra prosjektets egne data? Svaret er nei.

    Energibalansens elpost fordeles på rene elbiler og ladbare hybrider. Antar man
    en intensitet for de rene elbilene, følger hybridenes elektriske kjørelengde —
    og dermed utility factor — som residual. Tabellen viser hvor sterkt den
    residualen avhenger av antakelsen.

    Resultatet er grunnlaget for at utility factor behandles som ekstern
    sensitivitetsparameter (antakelsesregisteret), ikke som kalibrert størrelse.
    """
    eb = read_extract("energybalance_11561_road").copy()
    eb = eb[eb["ContentsCode"] == "EnergibalansenPJ"]
    eb["aar"] = eb["Tid"].astype(str).str[:4]
    ebp = eb.pivot_table(index="aar", columns="EnergiProdukt", values="value", aggfunc="sum")

    km = read_extract("km_12577")
    k = km[(km["ContentsCode"] == "Kjorelengde") & (km["Kjoretoytype"] == "0")]
    kmp = k.pivot_table(index="Tid", columns="DrivstoffType", values="value", aggfunc="sum")

    rows = []
    for aar in sorted(set(ebp.index) & set(kmp.index)):
        if EB_ELECTRICITY_CODE not in ebp.columns or pd.isna(ebp.loc[aar, EB_ELECTRICITY_CODE]):
            continue
        gwh = float(ebp.loc[aar, EB_ELECTRICITY_CODE]) * 1e9 / 3.6 / 1e6
        bev = float(kmp.loc[aar, "18"]) if "18" in kmp.columns else 0.0
        phev = float(sum(kmp.loc[aar, c] for c in ("14", "16")
                         if c in kmp.columns and pd.notna(kmp.loc[aar, c])))
        if not bev or not phev:
            continue
        for antatt in bev_intensity_range:
            rest_gwh = gwh - bev * antatt
            uf_el = (rest_gwh / antatt) / phev if rest_gwh > 0 else float("nan")
            rows.append({
                "kontroll": "utility_factor_identifikasjon", "periode": aar,
                "eb_elektrisitet_GWh": gwh, "km_rene_elbiler_mill": bev,
                "km_ladbare_hybrider_mill": phev,
                "antatt_elbil_kwh_per_km": antatt,
                "rest_til_hybrider_GWh": rest_gwh,
                "implisert_elandel_hybrid": uf_el,
            })
    df = pd.DataFrame(rows)
    df["merknad"] = (
        "En variasjon på ±20 prosent i antatt elbilintensitet spenner implisert elandel "
        "over hele det mulige intervallet og utenfor. Utility factor er derfor ikke "
        "identifiserbar fra disse dataene og må hentes eksternt"
    )
    return df
