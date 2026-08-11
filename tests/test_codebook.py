"""Kodeboken skal dekke dataene nøyaktig — verken mindre eller mer.

Dette er det som gjør en kodebok etterprøvbar framfor dekorativ: hver kode som
finnes i uttrekkene må være forklart, og ingen forklaring får vise til en kode
som ikke finnes i dataene.
"""
from __future__ import annotations

import os

import pandas as pd
import pytest

from veitransport_energi.codebook import COLUMNS, build_codebook
from veitransport_energi.tables import SPECS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CODEBOOK_CSV = os.path.join(ROOT, "data", "metadata", "codebook.csv")


@pytest.fixture(scope="module")
def cb():
    return build_codebook()


def test_kodeboken_pa_disk_er_i_takt_med_dataene(cb):
    """Den committede kodeboken skal svare til det koden genererer nå."""
    assert os.path.exists(CODEBOOK_CSV), "codebook.csv mangler — kjør python -m veitransport_energi.codebook"
    lagret = pd.read_csv(CODEBOOK_CSV, dtype=str).fillna("")
    generert = cb.astype(str).fillna("")
    assert list(lagret.columns) == COLUMNS
    pd.testing.assert_frame_equal(
        lagret.reset_index(drop=True), generert.reset_index(drop=True), check_dtype=False
    )


def test_hver_kode_i_uttrekkene_er_forklart(cb, extracts):
    """Ingen kode i dataene uten rad i kodeboken."""
    mangler = []
    for spec in SPECS:
        df = extracts[spec.name]
        del_cb = cb[cb["extract"] == spec.name]
        for dim in del_cb["dimension"].unique():
            if dim in ("Tid", "(tabell)") or dim not in df.columns:
                continue
            i_data = set(df[dim].dropna().astype(str).unique())
            i_kodebok = set(del_cb[del_cb["dimension"] == dim]["code"].astype(str))
            for kode in i_data - i_kodebok:
                mangler.append(f"{spec.name}.{dim}={kode}")
    assert not mangler, f"koder uten forklaring: {mangler[:10]}"


def test_ingen_forklaring_uten_data(cb, extracts):
    """Ingen rad i kodeboken som viser til en kode dataene ikke inneholder."""
    overflodige = []
    for spec in SPECS:
        df = extracts[spec.name]
        del_cb = cb[(cb["extract"] == spec.name) & (~cb["dimension"].isin(["Tid", "(tabell)"]))]
        for _, r in del_cb.iterrows():
            dim = r["dimension"]
            if dim not in df.columns:
                overflodige.append(f"{spec.name}.{dim} (dimensjon finnes ikke i uttrekket)")
                continue
            if str(r["code"]) not in set(df[dim].dropna().astype(str).unique()):
                overflodige.append(f"{spec.name}.{dim}={r['code']}")
    assert not overflodige, f"forklaringer uten data: {overflodige[:10]}"


def test_alle_statistikkvariabler_har_enhet(cb):
    cc = cb[cb["role"] == "statistikkvariabel"]
    assert len(cc) > 0
    uten = cc[cc["unit"].astype(str).str.strip().isin(["", "nan"])]
    assert uten.empty, f"statistikkvariabler uten enhet: {uten[['extract', 'code']].to_dict('records')}"


def test_etikettene_er_ikke_tomme(cb):
    relevante = cb[~cb["role"].isin(["tid", "tabellnote"])]
    tomme = relevante[relevante["code_label"].astype(str).str.strip().isin(["", "nan"])]
    vis = tomme[["extract", "dimension", "code"]].head().to_dict("records")
    assert tomme.empty, f"koder uten etikett: {vis}"


def test_kodeboken_fanger_en_kode_som_forsvinner(cb, extracts):
    """Kontrollens skarphet: fjernes en kode fra dataene, skal dekningstesten reagere."""
    spec = next(s for s in SPECS if s.name == "sales_13585")
    df = extracts[spec.name]
    del_cb = cb[(cb["extract"] == spec.name) & (cb["dimension"] == "Produkter")]
    i_kodebok = set(del_cb["code"].astype(str))
    redusert = set(df["Produkter"].dropna().astype(str).unique()) - {"02b"}
    assert i_kodebok - redusert == {"02b"}, "testen skal isolere nøyaktig den fjernede koden"


def test_tabellnotene_er_med(cb):
    """De tyngste tolkningsforbeholdene skal stå i kodeboken, ikke bare i rådataene."""
    noter = cb[cb["role"] == "tabellnote"]
    assert len(noter) > 0
    tekst = " ".join(noter["note"].astype(str))
    assert "hovedsakelig hybrid" in tekst, "07849-noten om at «annet drivstoff» er hybrider mangler"
    assert "ikke kan sammenlignes med tidligere" in tekst or "ikkje kan samanliknast" in tekst, \
        "11174-noten om 2020-bruddet mangler"
    assert noter["note"].str.strip().ne("").all()
