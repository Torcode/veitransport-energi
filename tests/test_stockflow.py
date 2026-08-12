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


def test_aldersdefinisjonen_har_et_brudd_mellom_2023_og_2024():
    """Funn som korrigerer D-0025: kohortsporing over grensen er ugyldig.

    Andelen av fire årganger førstegangsregistreringer som gjenfinnes i «under
    4 år», er stabil fra 2008 til 2023 og hopper så. Bruddet er ikke omtalt i
    tabellens noter.
    """
    from veitransport_energi.survival import definition_break_check

    d = definition_break_check("personbiler")
    for_brudd = d[~d["etter_brudd"]]["dekningsforhold"]
    etter = d[d["etter_brudd"]]["dekningsforhold"]
    assert for_brudd.max() < 0.80, "forholdet før bruddet skal ligge klart under 0,8"
    assert etter.min() > 0.85, "forholdet etter bruddet skal ligge klart over 0,85"
    assert etter.min() - for_brudd.max() > 0.10, "hoppet skal være entydig"


def test_bruddoverganger_utelates_og_gir_renere_kurve():
    """Uten avgrensningen framstår definisjonsendringen som fallende overlevelse."""
    from veitransport_energi.survival import survival_curve as sc

    ren = sc("personbiler").set_index("fra_alder")
    med = sc("personbiler", include_break=True).set_index("fra_alder")
    assert ren["antall_aar"].max() < med["antall_aar"].max(), "avgrensningen skal fjerne år"
    for alder in ("4 - 7 år", "8 - 11 år"):
        assert ren.loc[alder, "rate_std"] < med.loc[alder, "rate_std"], (
            f"spredningen for {alder} skal falle når bruddoverganger utelates"
        )


def test_totalsummen_i_aldersdataene_er_uendret_over_bruddet():
    """Det er aldersfordelingen som er lagt om, ikke bestanden — viktig for tolkningen."""
    from veitransport_energi.datasets import read_extract
    from veitransport_energi.survival import age_distribution

    p = age_distribution("personbiler")
    st = read_extract("stock_07849")
    tot = st[st["ContentsCode"] == "Personbil1"].groupby("Tid")["value"].sum()
    for aar in ("2023", "2024", "2025"):
        avvik = abs(p.loc[aar].sum() / tot[aar] - 1)
        assert avvik < 0.02, f"totalsummen avviker {avvik:.1%} i {aar}"
