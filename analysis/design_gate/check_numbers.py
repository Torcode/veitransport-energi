"""Fase 0-kontroll: alle tall sitert i docs/01_design_gate.md (og charterets nøkkeltall)
skal stamme fra results/design_gate_results.json og data/metadata-CSV-ene skal være gyldige.

Kjør med PLANT_FAIL=1 for å demonstrere at kontrollen faktisk kan feile
(planter én bevisst gal forventning).
"""
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
R = json.load(open(os.path.join(HERE, "results", "design_gate_results.json"), encoding="utf-8"))

FAILS = []


def check(navn, faktisk, ventet, tol=0.05):
    ok = abs(faktisk - ventet) <= tol
    status = "OK  " if ok else "FEIL"
    print(f"[{status}] {navn}: dokument={ventet} resultat={round(faktisk, 4)}")
    if not ok:
        FAILS.append(navn)


A = R["A_skjot_03687_vs_11174_2010M01_2016M07"]
check("A bensin snittforhold", A["bensin(03 vs 03)"]["mean_ratio"], 0.9993, 0.0001)
check("A bensin maks avvik %", A["bensin(03 vs 03)"]["max_abs_pct_diff"], 5.3, 0.05)
check("A bensin andel mnd >1 %", A["bensin(03 vs 03)"]["share_months_abs_diff_gt_1pct"] * 100, 2.5, 0.1)
check("A bensin vekstkorr", A["bensin(03 vs 03)"]["growth_corr"], 0.993, 0.001)
check("A dieselsum snittforhold", A["diesel(04 vs 04a+04b)"]["mean_ratio"], 0.9996, 0.0001)
check("A dieselsum maks avvik %", A["diesel(04 vs 04a+04b)"]["max_abs_pct_diff"], 2.5, 0.05)
check("A dieselsum vekstkorr", A["diesel(04 vs 04a+04b)"]["growth_corr"], 0.998, 0.001)
check("A autodiesel alene forhold", A["diesel(04 vs 04b alene)"]["mean_ratio"], 0.763, 0.001)
check("A autodiesel alene median %", A["diesel(04 vs 04b alene)"]["median_abs_pct_diff"], 23.5, 0.05)
check("A total maks avvik %", A["total(00 vs 00)"]["max_abs_pct_diff"], 10.8, 0.05)
check("A total median %", A["total(00 vs 00)"]["median_abs_pct_diff"], 1.1, 0.05)
check("A total andel mnd >1 %", A["total(00 vs 00)"]["share_months_abs_diff_gt_1pct"] * 100, 50.6, 0.1)
check("A sesongkorr bensin", R["A_sesongprofil_korr"]["bensin"], 0.9998, 0.0001)
check("A sesongkorr diesel", R["A_sesongprofil_korr"]["diesel"], 0.9997, 0.0001)

B = R["B_skjot_11174_vs_13585_2022M01"]
for prod in ["bensin", "autodiesel", "anleggsdiesel"]:
    check(f"B petroleum {prod} avvik = 0", B["Petroleum"][f"{prod}_pct_diff"], 0.0, 1e-9)
check("B total autodiesel avvik %", B["Total"]["autodiesel_pct_diff"], 2.2, 0.05)
check("B total anleggsdiesel avvik %", B["Total"]["anleggsdiesel_pct_diff"], 1.4, 0.05)

check("C 2021-prikkede celler ('..')", R["C_13585_status_2021"][".."], 96, 0)
check("C petroleumsdekning 2021", R["C_13585_andel_ikke_prikket_per_aar"]["Petroleum"]["2021"], 1.0, 0)
check("C rent bio autodiesel 2025 %", R["C_bioandel_2025_prosent_av_totalvolum"]["autodiesel_reint_bio"], 2.2, 0.05)

D = R["D_aarssalg_mill_liter"]
check("D bensin 2010", D["11174_2010"]["bensin"], 1625, 0.5)
check("D bensin 2019", D["11174_2019"]["bensin"], 1029, 0.5)
check("D bensin 2025", D["13585_2025_total"]["bensin"], 826, 0.5)
check("D autodiesel 2010", D["11174_2010"]["autodiesel"], 2523, 0.5)
check("D autodiesel 2019", D["11174_2019"]["autodiesel"], 2925, 0.5)
check("D autodiesel 2025", D["13585_2025_total"]["autodiesel"], 2353, 0.5)
# charter: autodieselfall innenfor 13585-segmentet (2022->2025), sitert som "om lag 20 prosent".
# Sammenligning over 2020-bruddet (f.eks. mot 2019) er bevisst IKKE brukt i offentlig tekst.
fall = (1 - D["13585_2025_total"]["autodiesel"] / D["13585_2022_total"]["autodiesel"]) * 100
check("charter: autodieselfall 2022->2025 ca. 20 %", fall, 20.0, 1.0)

N = R["D_nyreg_personbiler_elandel_pct"]
check("D el-andel nyreg 2015", N["2015"], 17.9, 0.05)
check("D el-andel nyreg 2025", N["2025"], 94.7, 0.05)
check("D fossile nye+bruktimport 2025", R["D_nyreg_personbiler_2025"]["fossil"], 4218, 0)
check("D bruktimport el-andel 2025", R["D_nyreg_2025_nye_vs_bruktimport"]["B"]["el_pct"], 68.1, 0.05)

BST = R["D_bestand_personbiler"]
check("D bestand 2025 el-andel %", BST["2025"]["el_andel_pct"], 32.2, 0.05)
check("D bestand 2025 el antall", BST["2025"]["el"], 945182, 0)

KM = R["D_kjorelengde_personbiler"]
check("D km el andel %", KM["el_andel_av_km_pct"], 36.6, 0.05)

IMP = R["D_implisitt_antall_12577_vs_bestand_07849"]
for f, ventet in [("el", 4.0), ("bensin", 5.8), ("diesel", 15.7)]:
    avvik = (IMP["implisitt_12577"][f] / IMP["bestand_07849"][f] - 1) * 100
    check(f"designport 8.3: implisitt vs bestand {f} +%", avvik, ventet, 0.05)

EB = R["D_energibalanse_veitransport_el_GWh"]
check("D EB el 2020 GWh", EB["2020"], 1089, 0.5)
check("D EB el 2024 GWh", EB["2024"], 2783, 0.5)
# charter: "fra om lag 1,1 TWh i 2020 til om lag 2,8 TWh i 2024"
check("charter: EB el 2020 ~1,1 TWh", EB["2020"] / 1000, 1.1, 0.05)
check("charter: EB el 2024 ~2,8 TWh", EB["2024"] / 1000, 2.8, 0.05)

BV = R["D_implisitt_brennverdi_magnitudesjekk"]
check("D implisitt MJ/l bensin 2023", BV["2023"]["bensin_MJ_per_liter_implisitt"], 22.6, 0.05)
check("D implisitt MJ/l bensin 2024", BV["2024"]["bensin_MJ_per_liter_implisitt"], 24.6, 0.05)
check("D implisitt MJ/l autodiesel 2023", BV["2023"]["autodiesel_MJ_per_liter_implisitt"], 32.2, 0.05)
check("D implisitt MJ/l autodiesel 2024", BV["2024"]["autodiesel_MJ_per_liter_implisitt"], 32.6, 0.05)

# charter: "halvert siden 2010" (bensin)
check("charter: bensin 2025/2010 ~0,5", D["13585_2025_total"]["bensin"] / D["11174_2010"]["bensin"], 0.5, 0.02)

if os.environ.get("PLANT_FAIL") == "1":
    check("PLANTET FEIL (demonstrasjon): bensin 2010", D["11174_2010"]["bensin"], 9999, 0.5)

# CSV-gyldighet
sr = pd.read_csv(os.path.join(ROOT, "data", "metadata", "source_register.csv"))
um = pd.read_csv(os.path.join(ROOT, "data", "metadata", "unit_map.csv"))
VENTET_SR = ["source_id", "utgiver", "tabell_dokument", "url", "variabel", "definisjon", "enhet",
             "frekvens", "geografisk_niva", "tidsdekning", "uttrekksdato", "revisjonsstatus",
             "lisens", "transformasjoner", "kontrollstatus", "kjente_begrensninger"]
VENTET_UM = ["original_variabel", "original_enhet", "onsket_enhet", "konvertering",
             "kilde_konvertering", "usikkerhet", "kontrollstatus"]
ok_sr = list(sr.columns) == VENTET_SR and len(sr) >= 20 and sr["source_id"].is_unique
ok_um = list(um.columns) == VENTET_UM and len(um) >= 12
print(f"[{'OK  ' if ok_sr else 'FEIL'}] source_register.csv: 16 avtalte kolonner, {len(sr)} rader, unike id-er")
print(f"[{'OK  ' if ok_um else 'FEIL'}] unit_map.csv: 7 avtalte kolonner, {len(um)} rader")
if not ok_sr:
    FAILS.append("source_register")
if not ok_um:
    FAILS.append("unit_map")

print()
if FAILS:
    print(f"RESULTAT: {len(FAILS)} kontroll(er) FEILET: {FAILS}")
    sys.exit(1)
print("RESULTAT: alle kontroller besto.")
