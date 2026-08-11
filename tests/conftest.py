"""Fellesfixturer: tester kjører UTEN nettverk, på committede uttrekk i data/extracts.

Innlesingen går gjennom pakkens egen `read_extract`, slik at testene ser dataene
nøyaktig slik analysekoden gjør — særlig med klassifikasjonskodene som tekst
(«00» skal ikke bli 0).
"""
from __future__ import annotations

import pandas as pd
import pytest

from veitransport_energi.datasets import read_all


@pytest.fixture(scope="session")
def extracts() -> dict[str, pd.DataFrame]:
    return read_all()
