"""Innlesingen skal bevare kodene som tekst — dette er en stille feilkilde."""
from __future__ import annotations

import pandas as pd
import pytest

from veitransport_energi.datasets import extract_path, read_extract


def test_ledende_nuller_bevares(extracts):
    koder = set(extracts["sales_13585"]["Produkter"].unique())
    assert "00" in koder and "01" in koder and "02a" in koder
    assert 0 not in koder and "0" not in koder
    assert set(extracts["sales_13585"]["Kjopegrupper"].unique()) == {"00"}


def test_standardinnlesing_ville_odelagt_kodene():
    """Kontrollens begrunnelse: pandas' standard gjør «00» om til 0.

    Testen dokumenterer feilen read_extract er laget for å hindre, og feiler
    dersom den antakelsen en dag ikke lenger holder.
    """
    naiv = pd.read_csv(extract_path("sales_13585"))
    assert 0 in set(naiv["Kjopegrupper"].unique()), "pandas tolker ikke lenger «00» som tall"
    assert "00" not in set(naiv["Kjopegrupper"].astype(object).unique())


def test_value_er_numerisk_og_status_er_tekst(extracts):
    df = extracts["sales_13585"]
    assert pd.api.types.is_numeric_dtype(df["value"])
    assert df["status"].isna().sum() == 0
    assert (df["status"] == "..").sum() > 0  # 2021 er prikket


def test_ukjent_uttrekk_gir_tydelig_feil():
    with pytest.raises(KeyError, match="ukjent uttrekk"):
        read_extract("finnes_ikke")
