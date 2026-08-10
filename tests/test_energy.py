"""Energifaktorene skal være nøyaktig kildens verdier, og omregningen skal følge av dem."""
from __future__ import annotations

import pytest

from veitransport_energi import energy


def test_faktorer_er_kildens_verdier():
    # SSB Notater 2018/45, vedlegg A, tabell A2 og A3 (lest 2026-08-10)
    assert energy.DENSITY_KG_PER_L["bensin"] == 0.74
    assert energy.DENSITY_KG_PER_L["autodiesel_fossil"] == 0.84
    assert energy.NCV_GJ_PER_TONN["bensin"] == 43.9
    assert energy.NCV_GJ_PER_TONN["autodiesel_fossil"] == 43.1
    assert energy.DENSITY_KG_PER_L["biodiesel"] == 0.88
    assert energy.NCV_GJ_PER_TONN["biodiesel"] == 36.8
    assert energy.DENSITY_KG_PER_L["bioetanol"] == 0.791
    assert energy.NCV_GJ_PER_TONN["bioetanol"] == 26.8


def test_mj_per_liter_er_avledet_ikke_hardkodet():
    for p in energy.NCV_GJ_PER_TONN:
        assert energy.MJ_PER_LITER[p] == pytest.approx(
            energy.NCV_GJ_PER_TONN[p] * energy.DENSITY_KG_PER_L[p], abs=1e-12
        )
    assert energy.MJ_PER_LITER["bensin"] == pytest.approx(32.486, abs=1e-3)
    assert energy.MJ_PER_LITER["autodiesel_fossil"] == pytest.approx(36.204, abs=1e-3)


def test_omregning_mill_liter_til_gwh():
    gwh = energy.mill_liter_to_gwh(1.0, "bensin")
    assert gwh == pytest.approx(1.0 * 1e6 * 32.486 / 3.6 / 1e6, rel=1e-4)
    with pytest.raises(KeyError):
        energy.mill_liter_to_gwh(1.0, "finnes_ikke")


def test_magnitude_mot_designportens_diagnostikk():
    """Designporten målte implisitt 32,2-32,6 MJ/l for autodiesel (EB/salg).

    Med kildens fossilfaktor 36,20 MJ/l svarer det til en energibærende
    fossilandel på om lag 89-90 prosent — konsistent med iblandet bio.
    Testen låser denne tolkningsrammen: implisitt faktor SKAL ligge under
    fossilfaktoren så lenge salgsvolumet inkluderer bio.
    """
    import json
    import os

    path = os.path.join(os.path.dirname(__file__), "..",
                        "analysis", "design_gate", "results", "design_gate_results.json")
    with open(path, encoding="utf-8") as f:
        r = json.load(f)
    for aar in ("2023", "2024"):
        impl = r["D_implisitt_brennverdi_magnitudesjekk"][aar]["autodiesel_MJ_per_liter_implisitt"]
        assert impl < energy.MJ_PER_LITER["autodiesel_fossil"]
        assert impl / energy.MJ_PER_LITER["autodiesel_fossil"] > 0.85
