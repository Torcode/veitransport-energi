"""Fase 0: Empiriske tester for designporten.

A: Skjøt 03687 vs 11174 i 79 overlappsmåneder (2010M01-2016M07)
B: Skjøt 11174 vs 13585 i den ene overlappsmåneden (2022M01)
C: Dekning/prikking i 13585 (2021-årgangen)
D: Nøkkelbilder: nyregistreringer, bestand, kjørelengder, energibalanse, implisitte faktorer

Alle resultater skrives til results/ og skal være eneste kilde for tall som
gjengis i docs/01_design_gate.md.
"""
import os
import json
import numpy as np
import pandas as pd

HERE = os.path.dirname(__file__)
EX = os.path.join(HERE, "extracts")
RES = os.path.join(HERE, "results")
os.makedirs(RES, exist_ok=True)

out = {}

# ---------- Last inn ----------
s03 = pd.read_csv(os.path.join(EX, "sales_03687.csv"), dtype={"PetroleumProd": str})
s11 = pd.read_csv(os.path.join(EX, "sales_11174.csv"), dtype={"PetroleumProd": str})
s13 = pd.read_csv(os.path.join(EX, "sales_13585.csv"), dtype={"Produkter": str})
fr = pd.read_csv(os.path.join(EX, "firstreg_14020.csv"), dtype={"DrivstoffType": str})
st = pd.read_csv(os.path.join(EX, "stock_07849.csv"), dtype={"DrivstoffType": str})
km = pd.read_csv(os.path.join(EX, "km_12577.csv"), dtype={"DrivstoffType": str, "Kjoretoytype": str})
eb = pd.read_csv(os.path.join(EX, "energybalance_11561_road.csv"))

# ---------- A: 03687 vs 11174 ----------
a3 = s03.pivot_table(index="Tid", columns="PetroleumProd", values="value")
a1 = s11.pivot_table(index="Tid", columns="PetroleumProd", values="value")
ovl = sorted(set(a3.index) & set(a1.index))
assert len(ovl) == 79, f"forventet 79 overlappsmåneder, fikk {len(ovl)}"
cmp = pd.DataFrame(index=ovl)
cmp["bensin_03687"] = a3.loc[ovl, "03"]
cmp["bensin_11174"] = a1.loc[ovl, "03"]
cmp["diesel_03687"] = a3.loc[ovl, "04"]
cmp["autodiesel_11174"] = a1.loc[ovl, "04b"]
cmp["anleggsdiesel_11174"] = a1.loc[ovl, "04a"]
cmp["dieselsum_11174"] = cmp["autodiesel_11174"] + cmp["anleggsdiesel_11174"]
cmp["total_03687"] = a3.loc[ovl, "00"]
cmp["total_11174"] = a1.loc[ovl, "00"]


def diffstats(x, y):
    r = y / x
    d = (y - x) / x * 100
    gx, gy = np.diff(np.log(x)), np.diff(np.log(y))
    return {
        "n": len(x),
        "mean_ratio": float(r.mean()),
        "mean_abs_pct_diff": float(d.abs().mean()),
        "median_abs_pct_diff": float(d.abs().median()),
        "max_abs_pct_diff": float(d.abs().max()),
        "share_months_abs_diff_gt_1pct": float((d.abs() > 1).mean()),
        "growth_corr": float(np.corrcoef(gx, gy)[0, 1]),
    }


splice_a = {
    "bensin(03 vs 03)": diffstats(cmp["bensin_03687"], cmp["bensin_11174"]),
    "diesel(04 vs 04a+04b)": diffstats(cmp["diesel_03687"], cmp["dieselsum_11174"]),
    "diesel(04 vs 04b alene)": diffstats(cmp["diesel_03687"], cmp["autodiesel_11174"]),
    "total(00 vs 00)": diffstats(cmp["total_03687"], cmp["total_11174"]),
}
cmp.to_csv(os.path.join(RES, "splice_monthly_03687_11174.csv"))
out["A_skjot_03687_vs_11174_2010M01_2016M07"] = splice_a

# Sesongprofil-korrelasjon (månedsgjennomsnitt av andel av årssum)
cmp2 = cmp.copy()
cmp2["mnd"] = [t[-2:] for t in cmp2.index]
prof = cmp2.groupby("mnd")[["bensin_03687", "bensin_11174", "diesel_03687", "dieselsum_11174"]].mean()
out["A_sesongprofil_korr"] = {
    "bensin": float(np.corrcoef(prof["bensin_03687"], prof["bensin_11174"])[0, 1]),
    "diesel": float(np.corrcoef(prof["diesel_03687"], prof["dieselsum_11174"])[0, 1]),
}

# ---------- B: 11174 vs 13585 i 2022M01 ----------
b = {}
m = "2022M01"
p11 = a1.loc[m]
for cc in ["Total", "Petroleum"]:
    p13 = s13[(s13["Tid"] == m) & (s13["ContentsCode"] == cc)].set_index("Produkter")["value"]
    b[cc] = {
        "bensin_11174": float(p11["03"]), "bensin_13585": float(p13["01"]),
        "bensin_pct_diff": float((p13["01"] - p11["03"]) / p11["03"] * 100),
        "autodiesel_11174": float(p11["04b"]), "autodiesel_13585": float(p13["02a"]),
        "autodiesel_pct_diff": float((p13["02a"] - p11["04b"]) / p11["04b"] * 100),
        "anleggsdiesel_11174": float(p11["04a"]), "anleggsdiesel_13585": float(p13["02b"]),
        "anleggsdiesel_pct_diff": float((p13["02b"] - p11["04a"]) / p11["04a"] * 100),
    }
out["B_skjot_11174_vs_13585_2022M01"] = b

# ---------- C: Dekning i 13585 ----------
cov = (s13.assign(aar=s13["Tid"].str[:4], has=s13["value"].notna())
          .groupby(["ContentsCode", "aar"])["has"].mean().unstack().round(3))
cov.to_csv(os.path.join(RES, "coverage_13585.csv"))
out["C_13585_andel_ikke_prikket_per_aar"] = {
    cc: {aar: float(v) for aar, v in row.items()} for cc, row in cov.iterrows()
}
stat2021 = s13[(s13["Tid"].str[:4] == "2021")]["status"].value_counts().to_dict()
out["C_13585_status_2021"] = {str(k): int(v) for k, v in stat2021.items()}

# Bio-andel i autodiesel og bensin, siste hele år (2025), fra 13585
s13p = s13.pivot_table(index=["Tid"], columns=["ContentsCode", "Produkter"], values="value")
y2025 = s13p[[c for c in s13p.columns]].loc[[t for t in s13p.index if t.startswith("2025")]].sum()
try:
    bio_ad = float(y2025[("Biodrivstoff", "02a")]) / float(y2025[("Total", "02a")]) * 100
    bio_bb = float(y2025[("Biodrivstoff", "01")]) / float(y2025[("Total", "01")]) * 100
    out["C_bioandel_2025_prosent_av_totalvolum"] = {
        "autodiesel_reint_bio": round(bio_ad, 2), "bilbensin_reint_bio": round(bio_bb, 2),
        "NB": "Reint bio = eige maltall; iblanda bio ligg i petroleumsvolumet og kan ikkje skiljast ut her.",
    }
except KeyError:
    pass

# Årssummer salg (nivåbilde til designdokumentet)
ann11 = s11.assign(aar=s11["Tid"].str[:4]).groupby(["aar", "PetroleumProd"])["value"].sum().unstack()
ann13 = (s13[s13["ContentsCode"] == "Total"].assign(aar=lambda d: d["Tid"].str[:4])
         .groupby(["aar", "Produkter"])["value"].sum().unstack())
ann11.to_csv(os.path.join(RES, "annual_sales_11174.csv"))
ann13.to_csv(os.path.join(RES, "annual_sales_13585_total.csv"))
out["D_aarssalg_mill_liter"] = {
    "11174_2010": {"bensin": round(float(ann11.loc["2010", "03"]), 1), "autodiesel": round(float(ann11.loc["2010", "04b"]), 1)},
    "11174_2019": {"bensin": round(float(ann11.loc["2019", "03"]), 1), "autodiesel": round(float(ann11.loc["2019", "04b"]), 1)},
    "13585_2022_total": {"bensin": round(float(ann13.loc["2022", "01"]), 1), "autodiesel": round(float(ann13.loc["2022", "02a"]), 1)},
    "13585_2025_total": {"bensin": round(float(ann13.loc["2025", "01"]), 1), "autodiesel": round(float(ann13.loc["2025", "02a"]), 1)},
}

# ---------- D: Nyregistreringer 14020 ----------
fr["aar"] = fr["Tid"].str[:4]
frp = (fr[fr["ContentsCode"] == "Personbiler"]
       .groupby(["aar", "DrivstoffType"])["value"].sum().unstack())
frp["sum"] = frp.sum(axis=1)
frp["el_andel_pct"] = frp["19"] / frp["sum"] * 100
frp.to_csv(os.path.join(RES, "firstreg_personbiler_annual.csv"))
out["D_nyreg_personbiler_elandel_pct"] = {
    aar: round(float(frp.loc[aar, "el_andel_pct"]), 1)
    for aar in ["2010", "2015", "2020", "2023", "2024", "2025"] if aar in frp.index
}
out["D_nyreg_personbiler_2025"] = {
    "sum": int(frp.loc["2025", "sum"]), "el": int(frp.loc["2025", "19"]),
    "fossil": int(frp.loc["2025", "20"]), "hybrid": int(frp.loc["2025", "21"]),
}
# nye vs bruktimport, el-andel 2025
fr25 = fr[(fr["aar"] == "2025") & (fr["ContentsCode"] == "Personbiler")]
nb = fr25.groupby(["TypeRegistrering", "DrivstoffType"])["value"].sum().unstack()
out["D_nyreg_2025_nye_vs_bruktimport"] = {
    t: {"sum": int(r.sum()), "el_pct": round(float(r["19"] / r.sum() * 100), 1)}
    for t, r in nb.iterrows()
}

# ---------- D: Bestand 07849 ----------
stp = st[st["ContentsCode"] == "Personbil1"].pivot_table(index="Tid", columns="DrivstoffType", values="value")
stp["sum"] = stp.sum(axis=1)
stp["el_andel_pct"] = stp["5"] / stp["sum"] * 100
stp.to_csv(os.path.join(RES, "stock_personbiler_07849.csv"))
out["D_bestand_personbiler"] = {
    str(aar): {"sum": int(stp.loc[aar, "sum"]), "bensin": int(stp.loc[aar, "1"]),
               "diesel": int(stp.loc[aar, "2"]), "el": int(stp.loc[aar, "5"]),
               "annet_hovedsakelig_hybrid": int(stp.loc[aar, "6"]),
               "el_andel_pct": round(float(stp.loc[aar, "el_andel_pct"]), 1)}
    for aar in [2008, 2015, 2020, 2024, 2025]
}

# ---------- D: Kjørelengder 12577 ----------
kmp = km[(km["Kjoretoytype"] == "15")]
piv_tot = kmp[kmp["ContentsCode"] == "Kjorelengde"].pivot_table(index="Tid", columns="DrivstoffType", values="value")
piv_avg = kmp[kmp["ContentsCode"] == "GjsnittKjorelengde"].pivot_table(index="Tid", columns="DrivstoffType", values="value")
piv_tot.to_csv(os.path.join(RES, "km_total_personbiler_12577.csv"))
piv_avg.to_csv(os.path.join(RES, "km_avg_personbiler_12577.csv"))
sist = int(piv_avg.index.max())
out["D_kjorelengde_personbiler"] = {
    "siste_aar": sist,
    "gjsn_km": {"bensin": float(piv_avg.loc[sist, "1"]), "diesel": float(piv_avg.loc[sist, "2"]),
                "el": float(piv_avg.loc[sist, "18"]), "alle": float(piv_avg.loc[sist, "0"])},
    "total_mill_km": {"bensin": float(piv_tot.loc[sist, "1"]), "diesel": float(piv_tot.loc[sist, "2"]),
                      "el": float(piv_tot.loc[sist, "18"]), "alle": float(piv_tot.loc[sist, "0"])},
    "el_andel_av_km_pct": round(float(piv_tot.loc[sist, "18"] / piv_tot.loc[sist, "0"] * 100), 1),
}
# Implisitt antall kjøretøy (total/gjennomsnitt) vs bestand 07849 – konsistenskontroll
impl = {}
for code, navn in [("1", "bensin"), ("2", "diesel"), ("18", "el")]:
    n_impl = piv_tot.loc[sist, code] * 1e6 / piv_avg.loc[sist, code]
    impl[navn] = int(n_impl)
b07 = {"bensin": int(stp.loc[sist, "1"]), "diesel": int(stp.loc[sist, "2"]), "el": int(stp.loc[sist, "5"])} \
    if sist in stp.index else None
out["D_implisitt_antall_12577_vs_bestand_07849"] = {"aar": sist, "implisitt_12577": impl, "bestand_07849": b07,
    "NB": "12577 dekker kjoretoy som var registrert i lopet av aaret; 07849 er pr 31.12. Avvik ventes."}

# ---------- D: Energibalansen veitransport ----------
ebp = eb[eb["ContentsCode"] == "EnergibalansenGWh"].pivot_table(index="Tid", columns="EnergiProdukt_label", values="value")
ebp.to_csv(os.path.join(RES, "energybalance_road_gwh.csv"))
kol_el = [c for c in ebp.columns if c.strip().lower() == "elektrisitet"]
el_serie = ebp[kol_el[0]].dropna() if kol_el else pd.Series(dtype=float)
out["D_energibalanse_veitransport_el_GWh"] = {str(a): round(float(v), 0) for a, v in el_serie.items()
                                              if a in (2010, 2015, 2020, 2022, 2023, 2024)}
# Implisitt brennverdi-sjekk: energibalanse (PJ) / salg (mill. liter) for autodiesel og bensin
ebPJ = eb[eb["ContentsCode"] == "EnergibalansenPJ"].pivot_table(index="Tid", columns="EnergiProdukt_label", values="value")
impl_bv = {}
for aar in [2023, 2024]:
    try:
        bensin_PJ = float(ebPJ.loc[aar, "Bensin  (ekskl. bio)"])
        ad_PJ = float(ebPJ.loc[aar, "Autodiesel  (ekskl. bio)"])
        bensin_Ml = float(s13p[("Petroleum", "01")].loc[[t for t in s13p.index if t.startswith(str(aar))]].sum())
        ad_Ml = float(s13p[("Petroleum", "02a")].loc[[t for t in s13p.index if t.startswith(str(aar))]].sum())
        impl_bv[aar] = {
            "bensin_MJ_per_liter_implisitt": round(bensin_PJ * 1e9 / (bensin_Ml * 1e6), 2),
            "autodiesel_MJ_per_liter_implisitt": round(ad_PJ * 1e9 / (ad_Ml * 1e6), 2),
            "NB": "Petroleumsvolum 13585 inkluderer iblanda bio; energibalansen er ekskl. bio -> implisitt faktor er kun magnitudesjekk.",
        }
    except KeyError as e:
        impl_bv[aar] = f"mangler: {e}"
out["D_implisitt_brennverdi_magnitudesjekk"] = impl_bv

with open(os.path.join(RES, "design_gate_results.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
