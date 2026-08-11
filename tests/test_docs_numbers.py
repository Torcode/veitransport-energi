"""Tall som siteres i docs/ skal stamme fra designportens resultatfil (verifikasjonskontrakt 8).

Dette er fase 0-kontrollen (analysis/design_gate/check_numbers.py) videreført som
permanent test, avgrenset til de mest sentrale dokumenttallene.
"""
from __future__ import annotations

import json
import os

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="module")
def r():
    path = os.path.join(ROOT, "analysis", "design_gate", "results", "design_gate_results.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_skjot_a_bensin(r):
    a = r["A_skjot_03687_vs_11174_2010M01_2016M07"]["bensin(03 vs 03)"]
    assert a["mean_ratio"] == pytest.approx(0.9993, abs=1e-4)
    assert a["max_abs_pct_diff"] == pytest.approx(5.3, abs=0.05)


def test_skjot_a_dieselsum(r):
    a = r["A_skjot_03687_vs_11174_2010M01_2016M07"]["diesel(04 vs 04a+04b)"]
    assert a["mean_ratio"] == pytest.approx(0.9996, abs=1e-4)
    assert a["max_abs_pct_diff"] == pytest.approx(2.5, abs=0.05)


def test_skjot_b_petroleum_identisk(r):
    b = r["B_skjot_11174_vs_13585_2022M01"]["Petroleum"]
    for prod in ("bensin", "autodiesel", "anleggsdiesel"):
        assert b[f"{prod}_pct_diff"] == 0.0


def test_prikking_2021(r):
    assert r["C_13585_status_2021"][".."] == 96
    assert r["C_13585_andel_ikke_prikket_per_aar"]["Petroleum"]["2021"] == 1.0


def test_bestand_og_nyreg_nokkeltall(r):
    assert r["D_bestand_personbiler"]["2025"]["el"] == 945182
    assert r["D_bestand_personbiler"]["2025"]["el_andel_pct"] == pytest.approx(32.2, abs=0.05)
    assert r["D_nyreg_personbiler_elandel_pct"]["2025"] == pytest.approx(94.7, abs=0.05)


def test_energibalanse_el(r):
    assert r["D_energibalanse_veitransport_el_GWh"]["2024"] == pytest.approx(2783, abs=0.5)
