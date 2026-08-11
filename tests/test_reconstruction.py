"""Rekonstruksjonen skal være tolkbar — og nekte å produsere tall som ikke er det."""
from __future__ import annotations

import pytest

from veitransport_energi.reconstruction import (
    HYBRID_SPLIT_YEAR,
    calibrated_intensity,
    net_retirement,
)


@pytest.fixture(scope="module")
def nr():
    return net_retirement()


def test_avgangsratene_er_faglig_plausible(nr):
    """En bilpark skiller seg av med noen få prosent i året, ikke titalls."""
    ikke_el = nr[(nr["drivlinje"] == "ikke_elektrisk") & (nr["gruppe"] == "personbiler")]
    assert ikke_el["avgangsrate_pct"].between(2, 9).all(), (
        f"urimelige avgangsrater: {ikke_el['avgangsrate_pct'].describe()}"
    )


def test_hybridkategorien_beregnes_ikke_for_kildene_er_konsistente(nr):
    """Før 2017 førte kildene hybrider ulikt; residualen ville vært ren kategoriflytting."""
    tidlig = nr[(nr["drivlinje"].isin(["fossil_samlet", "hybrid_og_annet"]))
                & (nr["periode"].astype(int) < HYBRID_SPLIT_YEAR)]
    assert tidlig.empty, "hybrid/fossil-residual publiseres for tidlig"


def test_de_gjennomgaende_gruppene_dekker_hele_perioden(nr):
    for drivlinje in ("elektrisitet", "ikke_elektrisk"):
        d = nr[(nr["drivlinje"] == drivlinje) & (nr["gruppe"] == "personbiler")]
        assert d["periode"].min() == "2009"
        assert int(d["periode"].max()) >= 2024


def test_bestandsidentiteten_holder_eksakt(nr):
    """Residualen skal per definisjon lukke identiteten."""
    avvik = (nr["bestand_forrige"] + nr["tilgang"] - nr["nettoavgang"] - nr["bestand"]).abs()
    assert avvik.max() < 1e-9


def test_intensiteten_krever_at_hybridvalget_gjores_eksplisitt():
    """Uten utility factor skal begge grensene returneres, ikke ett tall."""
    uten = calibrated_intensity()
    assert set(uten["utility_factor"].unique()) == {0.0, 1.0}
    med = calibrated_intensity(utility_factor=0.5)
    assert set(med["utility_factor"].unique()) == {0.5}
    with pytest.raises(ValueError):
        calibrated_intensity(utility_factor=1.5)


def test_hybridvalget_endrer_konklusjonen_om_effektivitetsutviklingen():
    """Selve grunnen til at parameteren må være eksplisitt.

    Med UF=1 tilskrives ladbare hybriders kilometer forbrenningsmotoren, og
    bensinintensiteten faller fra 2010 til 2024. Med UF=0 gjør den det ikke.
    Et enkelttall uten oppgitt UF ville skjult at konklusjonen snur.
    """
    ci = calibrated_intensity()
    b = ci[ci["energibaerer"] == "bensin"].pivot_table(
        index="periode", columns="utility_factor", values="liter_per_mil")
    endring_uf1 = b.loc["2024", 1.0] / b.loc["2010", 1.0] - 1
    endring_uf0 = b.loc["2024", 0.0] / b.loc["2010", 0.0] - 1
    assert endring_uf1 < -0.25, "med UF=1 skal intensiteten falle klart"
    assert endring_uf0 > endring_uf1 + 0.2, "grensene skal gi vesentlig ulik konklusjon"


def test_elektrisitet_bruker_komplementet_av_utility_factor():
    """Ladbare hybriders kilometer kan ikke telle fullt i både drivstoff og strøm."""
    ci = calibrated_intensity(utility_factor=0.8)
    el = ci[ci["energibaerer"] == "elektrisitet"]
    bensin = ci[ci["energibaerer"] == "bensin"]
    assert el["ladbar_vekt"].round(6).eq(0.2).all()
    assert bensin["ladbar_vekt"].round(6).eq(0.8).all()


def test_elektrisitetsintensiteten_er_i_samsvar_med_uavhengig_maling():
    """NVEs måledatabaserte 0,2 kWh/km er en uavhengig kontroll av kalibreringen."""
    ci = calibrated_intensity(utility_factor=0.5)
    el = ci[(ci["energibaerer"] == "elektrisitet") & (ci["periode"] >= "2020")]
    assert el["kwh_per_km"].between(0.15, 0.35).all(), (
        f"kalibrert el-intensitet er urimelig: {el[['periode', 'kwh_per_km']].to_dict('records')}"
    )
