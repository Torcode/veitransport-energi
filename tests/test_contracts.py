"""Kontraktene skal (1) godkjenne faktiske uttrekk og (2) demonstrerbart kunne feile."""
from __future__ import annotations

import pandas as pd
import pytest

from veitransport_energi.contracts import ContractError, check_extract
from veitransport_energi.tables import SPECS, SPECS_BY_NAME


@pytest.mark.parametrize("spec", SPECS, ids=[s.name for s in SPECS])
def test_alle_uttrekk_bestar_kontraktene(extracts, spec):
    report = check_extract(extracts[spec.name], spec)
    assert report["rows"] > 0


def test_kontrakt_fanger_duplikatnokler(extracts):
    spec = SPECS_BY_NAME["sales_13585"]
    df = pd.concat([extracts[spec.name], extracts[spec.name].tail(1)], ignore_index=True)
    with pytest.raises(ContractError, match="duplikatnøkler"):
        check_extract(df, spec)


def test_kontrakt_fanger_negative_verdier(extracts):
    spec = SPECS_BY_NAME["sales_11174"]
    df = extracts[spec.name].copy()
    df.loc[df.index[0], "value"] = -1.0
    with pytest.raises(ContractError, match="negative"):
        check_extract(df, spec)


def test_kontrakt_fanger_hull_i_tidsaksen(extracts):
    spec = SPECS_BY_NAME["stock_07849"]
    df = extracts[spec.name]
    df = df[df["Tid"] != "2015"]
    with pytest.raises(ContractError, match="hull i tidsaksen"):
        check_extract(df, spec)


def test_kontrakt_fanger_ikke_numerisk_verdikolonne(extracts):
    spec = SPECS_BY_NAME["prices_09654"]
    df = extracts[spec.name].copy()
    df["value"] = df["value"].astype(str)
    with pytest.raises(ContractError, match="ikke numerisk"):
        check_extract(df, spec)


def test_kontrakt_fanger_prikket_celle_med_verdi(extracts):
    spec = SPECS_BY_NAME["sales_13585"]
    df = extracts[spec.name].copy()
    prikket = df["status"].fillna("").astype(str).str.strip() == ".."
    assert prikket.any(), "testforutsetning: 13585 skal ha prikkede celler (2021)"
    df.loc[df.index[prikket][0], "value"] = 123.0
    with pytest.raises(ContractError, match="prikkekode og verdi"):
        check_extract(df, spec)
