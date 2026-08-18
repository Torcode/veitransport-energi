"""Tilgangskilden er et valg, ikke en detalj (D-0036).

Forsidens hovedfunn er et forholdstall mellom tilgang og bestand. De to
førstegangsregistreringstabellene gir ulike svar på telleren, og forskjellen er
liten i prosent av alle nyregistreringer og stor i prosent av den fossile
tilgangen — som er nettopp den størrelsen funnet hviler på.

Testene her låser tre ting: at den publiserte tilgangstabellen er intern
konsistent, at kontrolltabellen faktisk viser forskjellen den er laget for å
vise, og at forsidens tall lar seg lese tilbake fra tabellen de er hentet fra.
"""
from __future__ import annotations

import os

import pandas as pd
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="module")
def tilgang() -> pd.DataFrame:
    return pd.read_csv(os.path.join(ROOT, "artifacts", "inflow_by_drivetrain.csv"),
                       dtype={"periode": str})


@pytest.fixture(scope="module")
def kilde() -> pd.DataFrame:
    return pd.read_csv(os.path.join(ROOT, "artifacts", "control_inflow_source.csv"),
                       dtype={"periode": str})


def test_fossilaggregatet_er_summen_av_bensin_og_diesel(tilgang):
    """Aggregatet skal være de to detaljerte kodene, ikke noe annet."""
    p = tilgang.pivot_table(index=["gruppe", "periode"], columns="drivlinje",
                            values="tilgang")
    ventet = p["bensin"] + p["diesel"]
    pd.testing.assert_series_equal(p["fossil_bensin_diesel"], ventet, check_names=False)


def test_bestandsidentiteten_lukker(tilgang):
    """bestand_forrige + tilgang - nettoavgang = bestand. Ellers er residualen feil."""
    d = tilgang.dropna(subset=["nettoavgang"])
    assert len(d) > 0
    lukket = d["bestand_forrige"] + d["tilgang"] - d["nettoavgang"]
    verst = (lukket - d["bestand_3112"]).abs().max()
    assert verst <= 1, f"identiteten lukker ikke; største avvik {verst}"


def test_de_to_nevnerne_er_ulike_og_begge_publisert(tilgang):
    """Forsiden siterer utgangsbestanden, figuren bruker inngangsbestanden.

    Blandes de, blir forholdet mellom to rater noe annet enn forholdet mellom
    antallene. Testen krever at begge finnes og at de faktisk skiller seg.
    """
    d = tilgang[(tilgang["gruppe"] == "personbiler")
                & (tilgang["drivlinje"] == "fossil_bensin_diesel")
                & (tilgang["periode"] == "2025")].iloc[0]
    assert d["tilgang_pct_av_bestand"] > d["tilgang_pct_av_bestand_forrige"], (
        "en krympende bestand gir høyere rate mot utgangs- enn mot inngangsbestanden"
    )


def test_totalene_stemmer_men_fossilkategorien_gjor_det_ikke(kilde):
    """Kontrollens hele poeng: enighet om totalen skjuler uenighet om kategorien.

    Uten dette funnet ville valget av tilgangskilde sett ut som en smakssak.
    Testen er skarp begge veier — den krever både at totalene er nære og at
    fossilkategorien ikke er det.
    """
    p = kilde[(kilde["gruppe"] == "personbiler") & (kilde["periode"] >= "2020")]
    i_alt = p[p["kategori"] == "i_alt"]["avvik_pct"].abs()
    fossil = p[p["kategori"] == "fossil"]["avvik_pct"].abs()
    assert i_alt.max() < 1.6, f"totalene spriker mer enn ventet: {i_alt.max():.2f} %"
    assert fossil.max() > 2.0, (
        f"fossilkategorien spriker ikke lenger ({fossil.max():.2f} %) — "
        "grunnlaget for D-0036 er borte, og beslutningen bør vurderes på nytt"
    )


def test_fossilavviket_er_stabilt_i_antall_og_voksende_i_prosent(kilde):
    """Formen på avviket er selve diagnosen.

    Et nesten konstant antall kjøretøy som blir en voksende andel, er et
    klassifikasjonsavvik under en kollapsende nevner — ikke en revisjon, som
    ville skalert med nivået.
    """
    f = kilde[(kilde["gruppe"] == "personbiler") & (kilde["kategori"] == "fossil")
              & (kilde["periode"] >= "2020")].sort_values("periode")
    antall = f["avvik_antall"].abs()
    assert antall.max() / antall.min() < 3, (
        f"avviket i antall er ikke stabilt: {antall.min()}-{antall.max()}"
    )
    assert f["avvik_pct"].abs().iloc[-1] > f["avvik_pct"].abs().iloc[0] * 3, (
        "den relative forskjellen vokser ikke lenger som beskrevet i merknaden"
    )
