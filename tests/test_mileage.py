"""Kjørelengde per kjøretøy, og kontrollen som avviste å gjøre den strukturell.

Dette er et negativt funn, og negative funn råtner lettere enn positive: ingen
merker at en avvist mekanisme stille blir tatt inn igjen. Testene låser derfor
både tallene som avviste den, og selve konklusjonen.
"""
from __future__ import annotations

import pandas as pd
import pytest

from veitransport_energi.mileage import mileage_identification, mileage_per_vehicle


@pytest.fixture(scope="module")
def km() -> pd.DataFrame:
    return mileage_per_vehicle()


@pytest.fixture(scope="module")
def ident() -> pd.DataFrame:
    return mileage_identification()


def test_fossile_biler_kjores_stadig_mindre_og_elbiler_mer(km):
    """Premisset for at størrelsen ikke kan antas konstant i en framskriving."""
    fin = km[km["oppdeling"] == "fin"].pivot_table(
        index="periode", columns="drivlinje", values="km_per_kjoretoy")
    for drivlinje in ("bensin", "diesel"):
        assert fin.loc["2025", drivlinje] < fin.loc["2016", drivlinje] * 0.9, (
            f"{drivlinje}: kjørelengde per kjøretøy skal ha falt merkbart siden 2016"
        )
    assert fin.loc["2025", "elektrisitet"] > fin.loc["2016", "elektrisitet"], (
        "elbilene skal ha gått motsatt vei"
    )


def test_dieselbiler_kjores_vesentlig_lenger_enn_bensinbiler(km):
    """Hvorfor sammensetningen av restparken betyr mer enn antallet."""
    fin = km[(km["oppdeling"] == "fin") & (km["periode"] == "2025")].set_index("drivlinje")
    forhold = fin.loc["diesel", "km_per_kjoretoy"] / fin.loc["bensin", "km_per_kjoretoy"]
    assert forhold > 1.4, f"forventet klart høyere kjørelengde for diesel, fikk {forhold:.2f}"


def test_nivasammenhengen_med_alder_ser_sterk_ut(ident):
    """Fellen. Uten dette tallet ville avvisningen i neste test virke overdreven."""
    d = ident.set_index("drivlinje")
    assert abs(d.loc["ikke_elektrisk", "korr_niva_km_mot_alder"]) > 0.9


def test_men_alder_og_kalendertid_er_naer_kollineaere(ident):
    d = ident.set_index("drivlinje")
    assert d.loc["ikke_elektrisk", "korr_alder_mot_tid"] > 0.95, (
        "kollineariteten er selve grunnen til at nivåsammenhengen ikke kan tolkes"
    )


def test_sammenhengen_forsvinner_i_differanser_og_er_ikke_identifisert(ident):
    """Kjernen: år med sterk aldring gir ikke sterkere fall enn år med svak.

    Blir denne grønn med en høy verdi en dag, er mekanismen identifisert og
    beslutningen kan gjøres om — men da skal det skje ved at noen ser tallet,
    ikke ved at antakelsen sniker seg inn i en modell.
    """
    for _, rad in ident.iterrows():
        assert abs(rad["korr_differanse_km_mot_alder"]) < 0.5, (
            f"{rad['drivlinje']}: differansesammenheng {rad['korr_differanse_km_mot_alder']:.3f}"
        )
    assert not ident["identifisert"].any()


def test_merknaden_sier_hva_konklusjonen_ble(ident):
    m = ident["merknad"].iloc[0]
    assert "førstedifferanser" in m
    assert "scenarioforutsetning" in m


def test_smaa_bestander_holdes_utenfor(km):
    """De tidligste elbilårene er for få kjøretøy til at forholdstallet betyr noe."""
    assert (km["bestand_3112"] >= 5_000).all()
    assert km["merknad"].str.contains("31.12").all(), (
        "forbeholdet om at bestanden er talt ved årsslutt skal følge tallet"
    )
