"""Kanonisk innlesing av uttrekkene.

Hvorfor denne modulen finnes: klassifikasjonskodene fra SSB er strenger, og
flere av dem ser ut som tall med ledende null — kjøpegruppe «00», produkt «01»,
drivstofftype «02a». Leses CSV-ene med pandas' standardinnstillinger, tolkes
«00» som tallet 0, og koden matcher ikke lenger metadata, kodebok eller
skjøteregler. Feilen er stille og forplanter seg til alt nedstrøms.

All lesing av `data/extracts/` skal derfor gå gjennom `read_extract()`, som
leser hver kolonne som tekst og konverterer bare `value` til tall.
"""
from __future__ import annotations

import os

import pandas as pd

from .tables import SPECS, SPECS_BY_NAME

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXTRACTS = os.path.join(ROOT, "data", "extracts")


def extract_path(name: str) -> str:
    if name not in SPECS_BY_NAME:
        raise KeyError(f"ukjent uttrekk '{name}'; kjente: {sorted(SPECS_BY_NAME)}")
    return os.path.join(EXTRACTS, f"{name}.csv")


def read_extract(name: str) -> pd.DataFrame:
    """Les ett uttrekk med koder som tekst og `value` som tall."""
    path = extract_path(name)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"uttrekk mangler: {path} — kjør `python -m veitransport_energi.build`"
        )
    df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["status"] = df["status"].fillna("")
    return df


def read_all() -> dict[str, pd.DataFrame]:
    """Alle uttrekk, nøklet på spesifikasjonsnavn."""
    return {spec.name: read_extract(spec.name) for spec in SPECS}
