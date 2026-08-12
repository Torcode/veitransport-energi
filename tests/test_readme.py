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
    with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
        return f.read()


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


def test_readme_viser_til_siste_beslutning(readme):
    """Statuslinjen skal peke på den nyeste beslutningen, ikke på en gammel."""
    with open(os.path.join(ROOT, "docs", "decision_log.md"), encoding="utf-8") as f:
        logg = f.read()
    siste = max(int(n) for n in re.findall(r"D-(\d{4})", logg))
    treff = re.search(r"Sist oppdatert etter beslutning D-(\d{4})", readme)
    assert treff, "README mangler henvisning til siste beslutning"
    assert int(treff.group(1)) == siste, (
        f"README viser til D-{treff.group(1)}, mens loggen er kommet til D-{siste:04d}"
    )


def test_figurene_readme_viser_til_finnes(readme):
    lokale = [r for r in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", readme)
              if not r.startswith(("http://", "https://"))]
    assert lokale, "README viser ingen figurer"
    for rel in lokale:
        assert os.path.exists(os.path.join(ROOT, rel)), f"README viser til {rel}, som mangler"


def test_hovedtallene_i_readme_stemmer_med_artefaktene(readme):
    """Tallene i «Hva vi vet» skal komme fra artefaktene, ikke fra hukommelsen."""
    h = pd.read_csv(os.path.join(ROOT, "artifacts", "historical_statistics.csv"))

    def elandel(variabel: str) -> str:
        d = h[(h["variabel"] == variabel) & (h["gruppe"] == "personbiler")
              & (h["periode"].astype(str).str[:4] == "2025")]
        andel = d.loc[d["drivlinje"] == "elektrisitet", "verdi"].sum() / d["verdi"].sum() * 100
        return f"{andel:.1f}".replace(".", ",")

    for variabel in ("bestand_3112", "kjorelengde_total"):
        assert elandel(variabel) in readme, f"README mangler {elandel(variabel)} for {variabel}"

    rec = pd.read_csv(os.path.join(ROOT, "artifacts", "control_energy_reconciliation.csv"))
    for aar, kolonne in ((2020, "salg_mill_liter_bensin"), (2025, "salg_mill_liter_bensin"),
                         (2025, "salg_mill_liter_autodiesel")):
        verdi = int(round(rec.loc[rec["periode"] == aar, kolonne].iloc[0]))
        assert f"{verdi:,}".replace(",", " ") in readme or str(verdi) in readme, (
            f"README mangler {verdi} ({kolonne} {aar})"
        )

    kohort = pd.read_csv(os.path.join(ROOT, "artifacts", "validation_cohort_model.csv"))
    verst = kohort[kohort["periode"] >= 2016]["avvik_pct"].abs().max()
    assert f"{verst:.2f}".replace(".", ",") in readme, "README mangler modellens største avvik"


def test_readme_lister_artefaktmappen_som_manifestet_kjenner():
    """Ingen resultatfil skal være usynlig fra forsiden.

    Lenken til artifacts/ er bare sann så lenge manifestet faktisk dekker mappen;
    ellers viser README til en katalog med upubliserte hovedtall i.
    """
    with open(os.path.join(ROOT, "artifacts", "release_manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    pa_disk = {n for n in os.listdir(os.path.join(ROOT, "artifacts")) if n.endswith(".csv")}
    assert pa_disk == set(manifest["artifacts"])
