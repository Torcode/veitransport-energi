"""Skjøtereglene fra designporten som regresjonstester (pkt. 3.1-3.2; D-0002/D-0003)."""
from __future__ import annotations

import pytest

from veitransport_energi.splice import (
    SpliceError,
    autodiesel_segments,
    bensin_series,
    continuous_autodiesel_series,
    dieselsum_series,
    overlap_stats,
)


def _pivots(extracts):
    s03 = extracts["sales_03687"].pivot_table(index="Tid", columns="PetroleumProd", values="value")
    s11 = extracts["sales_11174"].pivot_table(index="Tid", columns="PetroleumProd", values="value")
    return s03, s11


def test_skjot_bensin_03687_mot_11174(extracts):
    s03, s11 = _pivots(extracts)
    stats = overlap_stats(s03["03"], s11["03"])
    assert stats["n"] == 79
    assert stats["median_abs_pct_diff"] <= 0.01
    assert abs(stats["mean_ratio"] - 1.0) < 0.005
    assert stats["growth_corr"] > 0.99


def test_skjot_dieselsum_03687_mot_11174(extracts):
    s03, s11 = _pivots(extracts)
    stats = overlap_stats(s03["04"], s11["04a"] + s11["04b"])
    assert stats["n"] == 79
    assert stats["median_abs_pct_diff"] <= 0.01
    assert stats["max_abs_pct_diff"] < 3.0
    assert stats["growth_corr"] > 0.99


def test_skjot_11174_mot_13585_petroleumsmaltall_identisk(extracts):
    s11 = extracts["sales_11174"].pivot_table(index="Tid", columns="PetroleumProd", values="value")
    s13 = extracts["sales_13585"]
    p13 = (s13[s13["ContentsCode"] == "Petroleum"]
           .pivot_table(index="Tid", columns="Produkter", values="value"))
    m = "2022M01"
    for old, new in [("03", "01"), ("04b", "02a"), ("04a", "02b")]:
        assert s11.loc[m, old] == p13.loc[m, new], f"petroleumsmåltallet avviker i {m} for {old}/{new}"


def test_bensinserie_er_kontinuerlig_og_segmentmerket(extracts):
    serie = bensin_series(extracts["sales_03687"], extracts["sales_11174"], extracts["sales_13585"])
    assert serie["Tid"].is_unique
    assert serie["Tid"].min() == "1995M01"
    assert set(serie["segment"]) == {"03687", "11174", "13585_petroleum"}
    assert serie["value"].notna().all()


def test_dieselsum_stopper_for_bruddet(extracts):
    serie = dieselsum_series(extracts["sales_03687"], extracts["sales_11174"])
    assert serie["Tid"].max() == "2019M12"


def test_autodiesel_har_to_adskilte_segmenter(extracts):
    serie = autodiesel_segments(extracts["sales_11174"], extracts["sales_13585"])
    pre = serie[serie["segment"] == "autodiesel_2010_2019"]
    post = serie[serie["segment"] == "autodiesel_2020_"]
    assert pre["Tid"].max() == "2019M12"
    assert post["Tid"].min() == "2020M01"
    assert serie["Tid"].is_unique


def test_sammenhengende_autodieselserie_er_forbudt(extracts):
    with pytest.raises(SpliceError, match="2020"):
        continuous_autodiesel_series(extracts["sales_11174"], extracts["sales_13585"])
