"""Fellesfixturer: tester kjører UTEN nettverk, på committede uttrekk i data/extracts."""
from __future__ import annotations

import os

import pandas as pd
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXTRACTS = os.path.join(ROOT, "data", "extracts")


def _load(name: str) -> pd.DataFrame:
    path = os.path.join(EXTRACTS, f"{name}.csv")
    if not os.path.exists(path):
        pytest.fail(f"uttrekk mangler: {path} — kjør `python -m veitransport_energi.build` først")
    return pd.read_csv(path, dtype={c: str for c in ("PetroleumProd", "Produkter", "DrivstoffType",
                                                     "Kjoretoytype", "Tid")})


@pytest.fixture(scope="session")
def extracts() -> dict[str, pd.DataFrame]:
    from veitransport_energi.tables import SPECS

    return {spec.name: _load(spec.name) for spec in SPECS}
