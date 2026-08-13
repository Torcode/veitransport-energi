"""Fordelingen av drivstoffvolum på kjøretøygruppe.

Dette er leddet scenariodesignet manglet, og som avgjør om fase 5 kan levere
etterspørsel i liter eller bare kjøretøykilometer. Utledningen krever ingen
antatt utslippsfaktor — CO2 per liter er en egenskap ved drivstoffet — men den
hviler på at gruppene faktisk summerer til kildens eget total, og på at kildens
statuskoder tolkes riktig. Begge deler er testet her.
"""
from __future__ import annotations

import pandas as pd
import pytest

from veitransport_energi.fuelsplit import volume_shares, volume_vs_distance


@pytest.fixture(scope="module")
def andeler() -> pd.DataFrame:
    return volume_shares()


@pytest.fixture(scope="module")
def sammenligning() -> pd.DataFrame:
    return volume_vs_distance()


def test_gruppene_summerer_til_kildens_eget_total(andeler):
    """Uten dette er andelene ikke andeler av noe.

    Kontrollen går mot utslippsregnskapets egen veitrafikkpost, ikke mot summen
    av delene — nettopp for at en gruppe som mangler, skal gi utslag.
    """
    assert (andeler["sum_kontroll_pct"] - 100).abs().max() < 0.5, (
        f"største avvik fra kildens total: "
        f"{(andeler['sum_kontroll_pct'] - 100).abs().max():.2f} prosentpoeng"
    )


def test_motorsykler_har_ingen_diesel_og_det_er_null_ikke_manglende(andeler):
    """Statuskoden «.» betyr at kategorien ikke finnes, ikke at tallet mangler.

    Behandles den som manglende, forsvinner alle dieselår fra tabellen. Behandles
    et faktisk manglende år som null, telles et uferdig regnskap med. Testen
    låser at skillet er gjort.
    """
    diesel = andeler[andeler["energibaerer"] == "diesel"]
    assert not diesel.empty, "dieselårene er forsvunnet — statuskoden «.» tolkes som manglende"
    assert (diesel["andel_motorsykler_pct"] == 0).all()
    assert diesel["periode"].max() >= "2024", "siste publiserte år mangler"


def test_siste_uferdige_aar_er_utelatt(andeler):
    """Utslippsregnskapet publiseres senere enn salgsstatistikken.

    Året der gruppene har status «:» skal ikke gi en rad med andeler regnet fra
    ufullstendige tall.
    """
    assert "2025" not in set(andeler["periode"]), (
        "et år uten publisert gruppefordeling er tatt med"
    )


def test_personbilenes_volumandel_av_diesel_er_langt_lavere_enn_kilometerandelen(sammenligning):
    """Funnet som avgjør hva fase 5 kan påstå om autodiesel.

    Personbilene kjører over halvparten av dieselkilometerne, men bruker bare
    omkring en tredel av dieselen. Forskjellen er tunge kjøretøys forbruk per
    kilometer, og den er stor nok til at en framskriving basert på kilometer
    ville vært misvisende som etterspørselsanslag.
    """
    d = sammenligning[sammenligning["energibaerer"] == "diesel"].set_index("periode")
    siste = d.index.max()
    assert d.loc[siste, "andel_personbiler_pct_km"] > 50.0
    assert d.loc[siste, "andel_personbiler_pct_volum"] < 40.0
    assert d.loc[siste, "differanse_km_minus_volum_pp"] > 20.0, (
        "forskjellen mellom kilometer- og volumandel skal være stor for diesel"
    )


def test_bensin_er_naer_men_ikke_identisk_i_de_to_maalene(sammenligning):
    """For bensin er forskjellen liten — men den er ikke null, og grunnen er motorsykler."""
    d = sammenligning[sammenligning["energibaerer"] == "bensin"].set_index("periode")
    siste = d.index.max()
    differanse = d.loc[siste, "differanse_km_minus_volum_pp"]
    assert 3.0 < differanse < 15.0, f"uventet differanse for bensin: {differanse:.1f} prosentpoeng"


def test_tunge_kjoretoy_dominerer_dieselvolumet(sammenligning):
    d = sammenligning[sammenligning["energibaerer"] == "diesel"]
    assert d[d["periode"] == d["periode"].max()]["andel_tunge_pct"].iloc[0] > 40.0


def test_merknaden_sier_at_ingen_utslippsfaktor_er_antatt(andeler):
    """Metodens viktigste egenskap skal følge tallet, ikke bare stå i en docstring."""
    m = andeler["merknad"].iloc[0]
    assert "ingen utslippsfaktor" in m
    assert "fossilt" in m or "Biogent" in m or "biogent" in m
    assert "ikke identisk med prosjektets varebilgruppe" in m
