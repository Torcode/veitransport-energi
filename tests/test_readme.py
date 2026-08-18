"""README skal ikke kunne bli usann uten at noe blir rødt.

Forrige versjon av denne filen oppga «fase 1 av 7», «29 tester» og «27 kilder»
mens repoet faktisk hadde fullført fase 3, hadde over hundre tester og 29 kilder.
Ingenting fanget det: tallene var skrevet inn for hånd, og en README er det første
en leser møter. Verifikasjonskontraktens punkt om at hovedtall ikke skal kopieres
manuelt mellom dokumenter, gjelder også forsiden.

Testene her leser tallene tilbake fra det de påstår noe om.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

import pandas as pd
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="module")
def readme() -> str:
    """README-teksten med typografisk minus normalisert til bindestrek.

    Teksten bruker ekte minustegn (U+2212) foran negative tall, som er riktig
    typografi. Testene sammenligner mot Pythons formatering, som bruker
    bindestrek — uten normaliseringen ville et korrekt tall sett feil ut.
    """
    with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
        return f.read().replace("\u2212", "-")


@pytest.fixture(scope="module")
def antall_tester() -> int:
    """Antall tester repoet faktisk har, hentet fra pytest selv."""
    # `-o addopts=` nuller prosjektets egen -q, som ellers gjør utskriften så kort
    # at totalen forsvinner og testen ville måttet gjette.
    kjor = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q",
                           "-o", "addopts=", "-p", "no:cacheprovider"],
                          capture_output=True, text=True, cwd=ROOT, timeout=900)
    treff = re.search(r"(\d+) tests? collected", kjor.stdout)
    assert treff, f"fant ikke antall tester i pytest-utskriften:\n{kjor.stdout[-800:]}"
    return int(treff.group(1))


def test_antall_tester_i_readme_stemmer(readme, antall_tester):
    oppgitt = {int(n) for n in re.findall(r"(\d+) tester", readme)}
    assert oppgitt, "README oppgir ikke antall tester"
    assert oppgitt == {antall_tester}, (
        f"README oppgir {sorted(oppgitt)} tester, pytest samler inn {antall_tester}"
    )


def test_antall_kilder_i_readme_stemmer(readme):
    kilder = pd.read_csv(os.path.join(ROOT, "data", "metadata", "source_register.csv"))
    treff = re.search(r"(\d+) kilder", readme)
    assert treff, "README oppgir ikke antall kilder"
    assert int(treff.group(1)) == len(kilder)


def test_antall_beslutninger_i_readme_stemmer(readme):
    """Lenken til beslutningsloggen oppgir et antall; det skal ikke drive fra loggen."""
    with open(os.path.join(ROOT, "docs", "decision_log.md"), encoding="utf-8") as f:
        logg = f.read()
    antall = len(re.findall(r"^\*\*D-\d{4} ", logg, re.MULTILINE))
    treff = re.search(r"(\d+) daterte beslutninger", readme)
    assert treff, "README oppgir ikke antall beslutninger"
    assert int(treff.group(1)) == antall, (
        f"README sier {treff.group(1)} beslutninger, loggen har {antall}"
    )


def test_figurene_readme_viser_til_finnes(readme):
    lokale = [r for r in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", readme)
              if not r.startswith(("http://", "https://"))]
    assert lokale, "README viser ingen figurer"
    for rel in lokale:
        assert os.path.exists(os.path.join(ROOT, rel)), f"README viser til {rel}, som mangler"


def _norsk(x: float, desimaler: int = 1) -> str:
    return f"{x:.{desimaler}f}".replace(".", ",")


def test_hovedfunnets_tall_stemmer_med_artefaktene(readme):
    """Forsidens hovedfunn skal komme fra artefaktene, ikke fra hukommelsen."""
    v = pd.read_csv(os.path.join(ROOT, "artifacts", "control_volume_vs_distance.csv"),
                    dtype={"periode": str})
    siste = v["periode"].max()
    d = v[v["periode"] == siste].set_index("energibaerer")
    for baerer, kolonner in (("diesel", ("andel_personbiler_pct_km",
                                         "andel_personbiler_pct_volum",
                                         "andel_tunge_pct")),
                             ("bensin", ("andel_innenfor_volum_pct",))):
        for kolonne in kolonner:
            assert _norsk(d.loc[baerer, kolonne]) in readme, (
                f"README mangler {kolonne} for {baerer} ({_norsk(d.loc[baerer, kolonne])})"
            )
    assert _norsk(d.loc["diesel", "andel_innenfor_volum_pct"]) in readme

    kohort = pd.read_csv(os.path.join(ROOT, "artifacts", "validation_cohort_model.csv"))
    verst = kohort[kohort["periode"] >= 2016]["avvik_pct"].abs().max()
    assert _norsk(verst, 2) in readme, "README mangler modellens største avvik"


def test_identifikasjonsfunnet_paa_forsiden_stemmer(readme):
    """Den negative konklusjonen om kjørelengde skal hvile på kontrolltabellen.

    Nettopp fordi den er negativ, er den lett å skrive om til noe sterkere eller
    svakere uten at noen merker det.
    """
    d = pd.read_csv(os.path.join(ROOT, "artifacts", "control_mileage_identification.csv"))
    rad = d[d["drivlinje"] == "ikke_elektrisk"].iloc[0]
    assert _norsk(rad["korr_niva_km_mot_alder"], 3) in readme, "nivåkorrelasjonen mangler"
    assert _norsk(rad["korr_differanse_km_mot_alder"], 2) in readme, (
        "differansekorrelasjonen mangler — den er selve begrunnelsen"
    )

    m = pd.read_csv(os.path.join(ROOT, "artifacts", "reconstruction_mileage_per_vehicle.csv"),
                    dtype={"periode": str})
    fin = m[m["oppdeling"] == "fin"].pivot_table(
        index="periode", columns="drivlinje", values="km_per_kjoretoy")
    for drivlinje in ("bensin", "diesel", "elektrisitet"):
        for aar in ("2016", "2025"):
            ventet = f"{int(round(fin.loc[aar, drivlinje], -1)):,}".replace(",", " ")
            assert ventet in readme, f"{drivlinje} {aar}: {ventet} km mangler på forsiden"


def test_avgrensningen_mot_autodiesel_staar_paa_forsiden(readme):
    """Den feilen en leser lettest gjør, skal være vanskelig å gjøre."""
    flat = re.sub(r"\s+", " ", readme)
    assert "ikke en framskriving av autodieselsalget" in flat


def test_readme_lister_artefaktmappen_som_manifestet_kjenner():
    """Ingen resultatfil skal være usynlig fra forsiden.

    Lenken til artifacts/ er bare sann så lenge manifestet faktisk dekker mappen;
    ellers viser README til en katalog med upubliserte hovedtall i.
    """
    with open(os.path.join(ROOT, "artifacts", "release_manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    pa_disk = {n for n in os.listdir(os.path.join(ROOT, "artifacts")) if n.endswith(".csv")}
    assert pa_disk == set(manifest["artifacts"])


def test_hovedfunnets_spaketall_stemmer_med_tilgangstabellen(readme):
    """Forsidens mest siterte setning hadde ingen testdekning før dette (D-0036).

    Tallene kom fra en beregning som aldri ble publisert, så de kunne ikke leses
    tilbake fra noe. Nå ligger de i `inflow_by_drivetrain.csv`, som er bygget på
    den detaljerte drivstoffklassifikasjonen — den samme som bestandstabellen
    bruker, slik at teller og nevner står på samme kodeverk.
    """
    d = pd.read_csv(os.path.join(ROOT, "artifacts", "inflow_by_drivetrain.csv"),
                    dtype={"periode": str})
    p = d[(d["gruppe"] == "personbiler") & (d["periode"] == "2025")].set_index("drivlinje")

    assert _norsk(p.loc["elektrisitet", "andel_av_tilgang_pct"]) in readme, "elandelen mangler"
    assert _norsk(p.loc["fossil_bensin_diesel", "andel_av_tilgang_pct"]) in readme, (
        "den fossile andelen av nyregistreringene mangler"
    )
    antall = f"{int(p.loc['fossil_bensin_diesel', 'tilgang']):,}".replace(",", " ")
    assert antall in readme, f"fossil tilgang ({antall} biler) mangler"
    assert _norsk(p.loc["fossil_bensin_diesel", "tilgang_pct_av_bestand"], 2) in readme, (
        "forholdstallet tilgang mot bestand mangler"
    )
    bestand = _norsk(p.loc["fossil_bensin_diesel", "bestand_3112"] / 1e6)
    assert f"{bestand} millioner" in readme, f"fossil bestand ({bestand} millioner) mangler"


def test_hver_bygget_figur_vises_et_sted(readme):
    """En figur som ingen ser, er ikke en leveranse — og var utgangspunktet her.

    Repoet hadde en figur bygget og registrert i sporet uten at den sto på
    forsiden, mens forsidens hovedfunn ikke hadde noen figur i det hele tatt.
    Testen krever at hver figur i sporet faktisk vises i README eller notatet.
    """
    spor_sti = os.path.join(ROOT, "figurer", "figurspor.json")
    if not os.path.exists(spor_sti):
        pytest.skip("figurer/figurspor.json mangler — kjør Rscript R/bygg_figurer.R")
    with open(spor_sti, encoding="utf-8") as f:
        spor = json.load(f)
    with open(os.path.join(ROOT, "notat", "hva_vi_vet.qmd"), encoding="utf-8") as f:
        notat = f.read()
    for navn in spor["figurer"]:
        assert navn in readme or navn in notat, (
            f"{navn} bygges, men vises verken på forsiden eller i notatet"
        )
