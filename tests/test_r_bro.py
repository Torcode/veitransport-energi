"""Broen mellom verktøysettene: leser R de samme tallene som Python?

Begrunnelsen for at prosjektet i det hele tatt har et R-lag, er at artefaktene
skal være brukbare uten prosjektets egen kode. Det er en påstand, og påstander
skal kunne feile. Denne testen kjører R-kontrollen som en fremmed ville gjort —
bare mot filene i artifacts/ — og krever at svarene er identiske med Pythons.

Om R mangler lokalt, hoppes testen over, slik at en Python-utvikler ikke blokkeres.
I CI settes `KREV_R=1`, og da er et hopp en feil: en kontroll som stille lar være
å kjøre, er ikke en kontroll, og merket i README ville lovet mer enn det holder.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess

import pandas as pd
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
KREVES = os.environ.get("KREV_R") == "1"


@pytest.fixture(scope="module")
def r_resultat(tmp_path_factory):
    if shutil.which("Rscript") is None:
        if KREVES:
            pytest.fail("KREV_R=1, men Rscript finnes ikke — R-broen ble ikke kontrollert")
        pytest.skip("Rscript ikke installert; R-broen kontrolleres i CI")
    ut = tmp_path_factory.mktemp("r") / "kontroll.json"
    kjor = subprocess.run(
        ["Rscript", os.path.join(ROOT, "R", "kontroll_artefakter.R"), str(ut)],
        capture_output=True, text=True, timeout=600, cwd=ROOT,
    )
    if kjor.returncode != 0:
        pytest.fail(f"R-kontrollen feilet:\n{kjor.stdout}\n{kjor.stderr}")
    with open(ut, encoding="utf-8") as f:
        return json.load(f)


def _hist() -> pd.DataFrame:
    return pd.read_csv(os.path.join(ROOT, "artifacts", "historical_statistics.csv"))


def _elandel(h: pd.DataFrame, variabel: str, aar: str) -> float:
    d = h[(h["variabel"] == variabel) & (h["gruppe"] == "personbiler")
          & (h["periode"].astype(str).str[:4] == aar)]
    return d.loc[d["drivlinje"] == "elektrisitet", "verdi"].sum() / d["verdi"].sum() * 100


def test_r_verifiserer_manifestet_uavhengig(r_resultat):
    """Kjernepåstanden: en fremmed toolchain kan bekrefte at leveransen er hel."""
    with open(os.path.join(ROOT, "artifacts", "release_manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    assert r_resultat["alle_sjekksummer_stemmer"] is True
    assert r_resultat["artefakter_kontrollert"] == len(manifest["artifacts"])


def test_r_og_python_leser_samme_hovedtall(r_resultat):
    h = _hist()
    assert r_resultat["rader_historisk"] == len(h)
    for nokkel, variabel in (("elandel_bestand_2025", "bestand_3112"),
                             ("elandel_kjorelengde_2025", "kjorelengde_total")):
        assert r_resultat[nokkel] == pytest.approx(_elandel(h, variabel, "2025"), abs=1e-9), (
            f"{nokkel}: R og Python leser ulikt"
        )


def test_r_leser_norske_tegn_som_tegn_ikke_som_byte(r_resultat):
    """Vakten mot stille tegnødeleggelse i figurtekst.

    I en locale uten UTF-8 tolker R kildefilene sine feil allerede under parsing:
    «å» og «ø» blir to byte hver, og figurtittelen kommer ut som «kj..relengde».
    Det skjedde under bygget her, og feilen så ut som en fontmangel.

    Prøvestrengen er derfor en litteral i R/design.R, ikke en verdi fra et
    artefakt. Skillet er avgjørende: readr merker artefakttekst som UTF-8 uansett
    locale, så en kontroll mot artefaktdata ville vært grønn hele veien mens
    figurene var ødelagt.

    Feilen er reprodusert: med `PYTHONCOERCECLOCALE=0`, uten LANG/LC_ALL/LC_CTYPE
    og med vakten i R/oppstart.R slått av, ryker alle fire testene her. Med vakten
    på i samme miljø passerer de. Merk at CPython selv setter LC_CTYPE=C.UTF-8 i
    normal drift (PEP 538), så uten den ekstra avslåingen kan ikke denne veien
    utløses fra pytest — det testen låser i vanlig kjøring, er at strengen R
    faktisk parset, er identisk med byte-innholdet i kildefilen.
    """
    kilde = os.path.join(ROOT, "R", "design.R")
    with open(kilde, encoding="utf-8") as f:
        linje = next(rad for rad in f if rad.startswith("TEGNPROVE <-"))
    ventet = linje.split('"')[1]
    assert r_resultat["utf8_locale"] is True
    assert r_resultat["tegnkontroll_tekst"] == ventet
    assert r_resultat["tegnkontroll_lengde"] == len(ventet), (
        f"R teller {r_resultat['tegnkontroll_lengde']} tegn, Python {len(ventet)} — "
        "R kjører i feil locale, og norske tegn blir ødelagt i figurene"
    )


def test_notatet_kan_bygges_og_henter_tallene_fra_artefaktene(tmp_path):
    """Notatet skal ikke kunne råtne uten at noe blir rødt.

    Et statusnotat med tall som ikke lenger stemmer med leveransen, er verre enn
    ingen notat. Testen kjører R-koden i dokumentet og krever at hovedtallene som
    kommer ut, er de samme som artefaktene inneholder — og at de er formatert med
    desimalkomma, slik designdokumentet krever for norsk tekst.

    Quarto-CLI-en er ikke installert her; testen kjører knitr-motoren, som er den
    som utfører R-koden. Selve Quarto-formateringen kontrolleres ikke av denne.
    """
    if shutil.which("Rscript") is None:
        if KREVES:
            pytest.fail("KREV_R=1, men Rscript finnes ikke — notatet ble ikke bygget")
        pytest.skip("Rscript ikke installert")
    ut = tmp_path / "notat.md"
    kjor = subprocess.run(
        ["Rscript", "-e",
         'knitr::opts_chunk$set(echo = FALSE, warning = FALSE, message = FALSE); '
         f'knitr::knit("hva_vi_vet.qmd", output = "{ut.as_posix()}", quiet = TRUE)'],
        capture_output=True, text=True, timeout=600, cwd=os.path.join(ROOT, "notat"),
    )
    if kjor.returncode != 0:
        pytest.fail(f"notatet lot seg ikke bygge:\n{kjor.stdout}\n{kjor.stderr}")
    tekst = ut.read_text(encoding="utf-8")

    h = _hist()
    for variabel in ("bestand_3112", "kjorelengde_total"):
        ventet = f"{_elandel(h, variabel, '2025'):.1f}".replace(".", ",")
        assert ventet in tekst, f"notatet mangler {ventet} for {variabel}"

    kohort = pd.read_csv(os.path.join(ROOT, "artifacts", "validation_cohort_model.csv"))
    verst = f"{kohort[kohort['periode'] >= 2016]['avvik_pct'].abs().max():.2f}".replace(".", ",")
    assert verst in tekst, f"notatet mangler modellens største avvik ({verst})"
    assert "32.2" not in tekst, "notatet bruker punktum som desimalskille i norsk tekst"


def test_r_gjengir_modellresultatene_uendret(r_resultat):
    kohort = pd.read_csv(os.path.join(ROOT, "artifacts", "validation_cohort_model.csv"))
    verst = kohort[kohort["periode"] >= 2016]["avvik_pct"].abs().max()
    assert r_resultat["storste_avvik_kohortmodell_pct"] == pytest.approx(verst, abs=1e-9)

    stab = pd.read_csv(os.path.join(ROOT, "artifacts",
                                    "control_survival_parameter_stability.csv"))
    for drivlinje in ("elektrisitet", "ikke_elektrisk"):
        d = stab[stab["drivlinje"] == drivlinje]["weibull_scale"]
        assert r_resultat["weibull_skala_spenn"][drivlinje] == [d.min(), d.max()]
