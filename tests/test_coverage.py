"""Estimandets dekning: hva fase 5 kan framskrive, og hva den ikke kan.

Tallene her er ikke en kuriositet — de avgjør hvilke påstander scenarioene har
lov til å bære. Testene låser den asymmetrien som bærer scenariodesignet, slik at
en senere revisjon av kilden ikke stille flytter grensen for hva som kan sies.
"""
from __future__ import annotations

import pandas as pd
import pytest

from veitransport_energi.coverage import estimand_coverage


@pytest.fixture(scope="module")
def dekning() -> pd.DataFrame:
    return estimand_coverage()


def test_andelene_summerer_til_hundre(dekning):
    sum_deler = (dekning["andel_innenfor_estimandet_pct"] + dekning["andel_utenfor_pct"])
    assert (sum_deler - 100).abs().max() < 1e-9


def test_bensin_er_naermest_utelukkende_personbiler(dekning):
    """Derfor kan bensinetterspørselen framskrives som en personbilhistorie."""
    d = dekning[(dekning["energibaerer"] == "bensin") & (dekning["periode"] >= "2015")]
    assert d["andel_personbiler_pct"].min() > 95.0, (
        f"laveste personbilandel for bensin: {d['andel_personbiler_pct'].min():.1f} %"
    )


def test_diesel_ligger_i_vesentlig_grad_utenfor_estimandet(dekning):
    """Derfor kan ikke totalt autodieselsalg framskrives fra denne modellen.

    Andelen personbiler av dieselkilometerne faller dessuten over tid, så
    avgrensningen blir strengere med årene, ikke løsere.
    """
    d = dekning[dekning["energibaerer"] == "diesel"].set_index("periode")
    assert d.loc["2025", "andel_personbiler_pct"] < 60.0
    assert d.loc["2025", "andel_utenfor_pct"] > 10.0, (
        "en ikke ubetydelig del av dieselkilometerne skal ligge utenfor estimandet"
    )
    assert d.loc["2025", "andel_personbiler_pct"] < d.loc["2015", "andel_personbiler_pct"], (
        "personbilandelen av dieselkilometerne skal falle over perioden"
    )


def test_elektrisitet_er_i_hovedsak_dekket_men_faller(dekning):
    d = dekning[dekning["energibaerer"] == "elektrisitet"].set_index("periode")
    assert d.loc["2025", "andel_innenfor_estimandet_pct"] > 90.0
    assert d.loc["2025", "andel_innenfor_estimandet_pct"] < d.loc["2015",
                                                                  "andel_innenfor_estimandet_pct"], (
        "elektrifiseringen av tyngre kjøretøy skal vise seg som fallende dekning"
    )


def test_merknaden_skiller_kilometer_fra_volum(dekning):
    """Forbeholdet skal følge tallet, ikke bare stå i en modul-docstring.

    Andelen er kilometer. Tunge kjøretøy bruker flere ganger mer diesel per
    kilometer, så volumandelen innenfor estimandet er lavere enn tallet viser.
    Uten dette forbeholdet ville 86 prosent lest som «vi dekker 86 prosent av
    autodieselen», og det gjør modellen ikke.
    """
    merknad = dekning["merknad"].iloc[0]
    assert "kjørte kilometer" in merknad
    assert "ikke av drivstoffvolum" in merknad
    assert dekning["merknad"].nunique() == 1
