"""Koblingskontrollen låser funnene som avgjør kjøretøyavgrensningen (D-0020)."""
from __future__ import annotations

import pytest

from veitransport_energi.linkage import (
    aggregate_identities,
    inflow_source_comparison,
    stock_vs_activity,
)


@pytest.fixture(scope="module")
def agg():
    return aggregate_identities()


@pytest.fixture(scope="module")
def sva():
    return stock_vs_activity()


@pytest.fixture(scope="module")
def inflow():
    return inflow_source_comparison()


def test_kjorelengdeaggregatene_er_interne_summer(agg):
    """Uten dette kan aggregatene ikke brukes til å bygge kjøretøygrupper."""
    verst = agg["avvik_pct"].abs().max()
    assert verst < 0.05, f"aggregat avviker fra summen av delene: {verst:.3f} %"


def test_varebiler_kobler_godt_mot_sma_og_store_varebiler(sva):
    """29+30 er den koblingen som faktisk svarer til bestandsvariabelen Varebil4."""
    v = sva[(sva["bestandsvariabel"] == "Varebil4") & (sva["kobling"] == "små + store varebiler (29+30)")]
    assert v["avvik_pct"].abs().max() < 8.0
    assert v["avvik_pct"].median() < 5.0


def test_sma_godsbiler_i_alt_er_en_darligere_kobling(sva):
    """Kontrollens skarphet: den brede gruppen treffer merkbart dårligere."""
    smal = sva[(sva["bestandsvariabel"] == "Varebil4")
               & (sva["kobling"] == "små + store varebiler (29+30)")]["avvik_pct"].abs().mean()
    bred = sva[(sva["bestandsvariabel"] == "Varebil4")
               & (sva["kobling"] == "små godsbiler i alt (00)")]["avvik_pct"].abs().mean()
    assert bred > smal + 5, f"forventet klart dårligere kobling for bred gruppe: {bred:.1f} mot {smal:.1f}"


def test_personbiler_har_systematisk_positivt_avvik(sva):
    """I bruk i året ligger over beholdning per 31.12 — forventet, og skal være stabilt."""
    p = sva[(sva["bestandsvariabel"] == "Personbil1") & (sva["kobling"] == "kun personbiler (20)")]
    assert (p["avvik_pct"] > 0).all(), "avviket skal være positivt i alle år"
    assert p["avvik_pct"].between(4, 9).all(), f"avviket er ikke stabilt: {p['avvik_pct'].describe()}"


def test_12906_reproduserer_14020_som_totalstorrelse(inflow):
    """De to registreringskildene skal beskrive samme størrelse før de deles opp."""
    assert inflow["personbiler_avvik_pct"].abs().max() < 2.5
    assert inflow["varecamp_avvik_pct"].abs().max() < 2.5


def test_bobilandelen_er_vesentlig_nok_til_a_bety_noe(inflow):
    """Grunnen til at 12906 trengs: 14020 blander bobiler inn i varebiltilgangen."""
    assert inflow["bobilandel_pct"].min() > 3.0
    assert inflow["bobilandel_pct"].max() > 8.0
