"""Modellkjernen: identiteten skal holde, valideringen skal ikke kunne lekke,
og overlevelseskurven skal være stabil nok til å bære en kohortmodell.
"""
from __future__ import annotations

import pytest

from veitransport_energi.stockflow import backcast, calibrate_rates, load_model_data, run
from veitransport_energi.survival import AGE_ORDER, age_distribution, survival_curve

KALIB_GROV = [str(a) for a in range(2010, 2016)]


@pytest.fixture(scope="module")
def bc_grov():
    return backcast("personbiler", "grov", KALIB_GROV, "2015", "2025")


@pytest.fixture(scope="module")
def bc_fin():
    return backcast("personbiler", "fin", ["2020", "2021", "2022"], "2022", "2025")


def test_identiteten_holder_i_modellkjoringen():
    data = load_model_data("personbiler", "fin")
    rater = calibrate_rates(data, ["2020", "2021", "2022"])
    ut = run(data, rater, "2022", "2025")
    for aar in ut.index[1:]:
        forrige = str(int(aar) - 1)
        ventet = ut.loc[forrige] + data.inflow.loc[aar] - rater * ut.loc[forrige]
        assert (ut.loc[aar] - ventet).abs().max() < 1e-6


def test_validering_med_lekkasje_avvises():
    """Kalibrering inne i valideringsvinduet er ikke validering."""
    with pytest.raises(ValueError, match="lekkasje"):
        backcast("personbiler", "fin", ["2020", "2023"], "2022", "2025")


def test_starttilstanden_er_observert(bc_fin):
    start = bc_fin[bc_fin["horisont_aar"] == 0]
    assert (start["avvik_pct"].abs() < 1e-9).all(), "modellen skal starte i observert tilstand"


def test_feilen_er_liten_men_voksende_paa_kort_horisont(bc_fin):
    """Tre års horisont: under seks prosent for hovedgruppene."""
    hoved = bc_fin[bc_fin["drivlinje"].isin(["bensin", "diesel", "elektrisitet", "hybrid"])]
    assert hoved["avvik_pct"].abs().max() < 6.0
    per_horisont = hoved.groupby("horisont_aar")["avvik_pct"].apply(lambda s: s.abs().mean())
    assert per_horisont.loc[3] > per_horisont.loc[1], "feilen skal vokse med horisonten"


def test_konstant_rate_svikter_systematisk_paa_lang_horisont(bc_grov):
    """Begrunnelsen for å vurdere kohortmodell (D-0025).

    Over ti år bommer den konstante raten i motsatt retning for de to gruppene,
    og feilen vokser monotont — det er signaturen til en rate som ikke er
    stasjonær når flåtens alderssammensetning endrer seg.
    """
    el = bc_grov[(bc_grov["drivlinje"] == "elektrisitet") & (bc_grov["horisont_aar"] == 10)]
    ikke_el = bc_grov[(bc_grov["drivlinje"] == "ikke_elektrisk") & (bc_grov["horisont_aar"] == 10)]
    assert el["avvik_pct"].iloc[0] < -5, "elbestanden skal undervurderes"
    assert ikke_el["avvik_pct"].iloc[0] > 5, "den ikke-elektriske skal overvurderes"


def test_aldersfordelingen_summerer_til_rimelig_bestand():
    p = age_distribution("personbiler")
    assert list(p.columns) == AGE_ORDER
    sum_2025 = p.loc["2025"].sum()
    assert 2.7e6 < sum_2025 < 3.1e6, f"urimelig totalbestand: {sum_2025:,.0f}"


def test_overlevelseskurven_er_stabil_nok_for_en_kohortmodell():
    kurve = survival_curve("personbiler")
    assert len(kurve) == len(AGE_ORDER) - 1
    assert kurve["antall_aar"].min() >= 10, "for få år til å vurdere stabilitet"
    assert kurve["stabil"].all(), (
        f"ustabile overganger: {kurve[~kurve['stabil']][['fra_alder', 'rate_std']].to_dict('records')}"
    )


def test_yngste_overgang_ligger_over_en_og_er_forklart():
    """Bruktimport, ikke overlevelse over 100 prosent — forbeholdet skal stå i dataene."""
    kurve = survival_curve("personbiler")
    yngst = kurve[kurve["fra_alder"] == "Under 4 år"].iloc[0]
    assert yngst["rate_snitt"] > 1.0
    assert "bruktimport" in yngst["merknad"]


def test_ratene_faller_med_alderen_etter_den_yngste():
    kurve = survival_curve("personbiler")
    etter = kurve[kurve["fra_alder"] != "Under 4 år"]["rate_snitt"].tolist()
    assert etter == sorted(etter, reverse=True), f"forventet fallende overlevelse: {etter}"
