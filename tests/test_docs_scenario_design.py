"""Tallene i scenariodesignet skal stamme fra artefaktene, ikke fra hukommelsen.

Designdokumentet er der scenarioenes avgrensning begrunnes, og begrunnelsen
hviler på konkrete tall. Blir ett av dem stående etter en dataoppdatering, er
avgrensningen begrunnet med noe som ikke lenger er sant. Testene leser tallene
tilbake fra kildene de påstås å komme fra.
"""
from __future__ import annotations

import os
import re

import pandas as pd
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOK = os.path.join(ROOT, "docs", "04_scenario_design.md")


@pytest.fixture(scope="module")
def tekst() -> str:
    """Dokumentteksten med linjeskift normalisert til mellomrom.

    Uten normaliseringen ville testene vært avhengige av hvor linjene brytes, og
    en ren ombrekking ville gitt rødt uten at noe faglig var endret.
    """
    with open(DOK, encoding="utf-8") as f:
        return re.sub(r"\s+", " ", f.read())


def _norsk(x: float, desimaler: int = 1) -> str:
    return f"{x:.{desimaler}f}".replace(".", ",")


def test_dekningstallene_stemmer_med_kontrolltabellen(tekst):
    d = pd.read_csv(os.path.join(ROOT, "artifacts", "control_estimand_coverage.csv"),
                    dtype={"periode": str})
    siste = d[d["periode"] == "2025"].set_index("energibaerer")
    for baerer in ("bensin", "diesel", "elektrisitet"):
        for kolonne in ("andel_personbiler_pct", "andel_varebiler_pct",
                        "andel_innenfor_estimandet_pct"):
            verdi = _norsk(siste.loc[baerer, kolonne])
            assert verdi in tekst, f"{baerer}/{kolonne}: {verdi} mangler i designdokumentet"


def test_elandelen_i_nyregistreringer_stemmer(tekst):
    from veitransport_energi.stockflow import load_model_data

    d = load_model_data("personbiler", "fin")
    andel = d.inflow.div(d.inflow.sum(axis=1), axis=0) * 100
    for aar in ("2019", "2025"):
        assert _norsk(andel.loc[aar, "elektrisitet"]) in tekst, (
            f"elandel {aar} ({_norsk(andel.loc[aar, 'elektrisitet'])}) mangler"
        )
    fossilt = andel.loc["2025", "bensin"] + andel.loc["2025", "diesel"]
    assert _norsk(fossilt) in tekst, f"fossil andel 2025 ({_norsk(fossilt)}) mangler"


def test_kjorelengde_per_kjoretoy_stemmer(tekst):
    """Tallene som begrunner at kjørelengde per kjøretøy ikke kan antas konstant."""
    h = pd.read_csv(os.path.join(ROOT, "artifacts", "historical_statistics.csv"),
                    dtype={"periode": str})
    km = h[(h["variabel"] == "kjorelengde_total") & (h["gruppe"] == "personbiler")]
    best = h[(h["variabel"] == "bestand_3112") & (h["gruppe"] == "personbiler")]
    k = km.pivot_table(index="periode", columns="drivlinje", values="verdi", aggfunc="sum")
    b = best.pivot_table(index="periode", columns="drivlinje", values="verdi", aggfunc="sum")

    def per_bil(drivlinje: str, aar: str) -> float:
        return k.loc[aar, drivlinje] * 1e6 / b.loc[aar, drivlinje]

    for drivlinje in ("bensin", "diesel", "elektrisitet"):
        for aar in ("2016", "2025"):
            hel = int(round(per_bil(drivlinje, aar), -1))
            ventet = f"{hel:,}".replace(",", " ")
            assert ventet in tekst, f"{drivlinje} {aar}: {ventet} km mangler i dokumentet"

    forhold = per_bil("diesel", "2025") / per_bil("bensin", "2025") - 1
    assert f"{forhold * 100:.0f} prosent lenger" in tekst, (
        f"forholdet diesel/bensin ({forhold * 100:.0f} %) mangler"
    )


def test_dokumentet_avviser_totalt_autodieselsalg_som_leveranse(tekst):
    """Den viktigste avgrensningen skal stå eksplisitt, ikke antydes."""
    assert "aldri totalt autodieselsalg" in tekst
    assert "ikke *volum*" in tekst or "ikke volum" in tekst or "*kilometer*, ikke" in tekst


def test_ingen_scenariobane_kalles_mest_sannsynlig(tekst):
    """Begrepsdisiplinen: et scenario er en betinget beregning, ikke en prognose.

    Uttrykket «mest sannsynlig» har lov til å stå i dokumentet ett sted: der det
    avvises. Testen krever at antallet forekomster er nøyaktig antallet inne i
    den avvisende setningen — dukker det opp en gang til, er det brukt påstående.
    """
    lav = tekst.lower()
    avvisning = "ingen av dem er «mest sannsynlig»"
    assert avvisning in lav, "dokumentet skal avvise «mest sannsynlig» eksplisitt"
    assert lav.count("mest sannsynlig") == 1, (
        "«mest sannsynlig» forekommer utenfor den avvisende setningen"
    )
    for forbudt in ("forventet bane", "prognose for", "vil bli"):
        assert forbudt not in lav, f"'{forbudt}' er prognosespråk om en scenariobane"


def test_volumandelene_i_korreksjonen_stemmer_med_kontrolltabellen(tekst):
    """Korreksjonen fra D-0033 skal hvile på tabellen, ikke på hukommelsen."""
    v = pd.read_csv(os.path.join(ROOT, "artifacts", "control_volume_vs_distance.csv"),
                    dtype={"periode": str})
    siste = v["periode"].max()
    d = v[v["periode"] == siste].set_index("energibaerer")
    for baerer in ("bensin", "diesel"):
        for kolonne in ("andel_innenfor_estimandet_pct", "andel_innenfor_volum_pct"):
            assert _norsk(d.loc[baerer, kolonne]) in tekst, (
                f"{baerer}/{kolonne} for {siste} mangler i korreksjonen"
            )
        differanse = _norsk(d.loc[baerer, "differanse_km_minus_volum_pp"])
        assert f"{differanse} pp" in tekst, f"differansen for {baerer} ({differanse}) mangler"

    a = pd.read_csv(os.path.join(ROOT, "artifacts", "control_fuel_volume_shares.csv"),
                    dtype={"periode": str})
    diesel = a[(a["energibaerer"] == "diesel") & (a["periode"] == siste)].iloc[0]
    assert _norsk(diesel["andel_tunge_pct"]) in tekst, "tunge kjøretøys volumandel mangler"
    bensin = a[(a["energibaerer"] == "bensin") & (a["periode"] == siste)].iloc[0]
    assert _norsk(bensin["andel_motorsykler_pct"]) in tekst, "motorsyklenes volumandel mangler"


def test_korreksjonen_er_synlig_og_ikke_en_stille_omskriving(tekst):
    """Prosjektets praksis: en rettet påstand skal stå med hva som ble strøket.

    Uten den ville leseren ikke kunne se at avgrensningen en gang var begrunnet
    med at fordelingen ikke lot seg fastsette.
    """
    assert "Korreksjon 2026-08-12" in tekst
    assert "kan ikke avgjøres fra prosjektets kilder" in tekst, (
        "korreksjonen skal gjengi det som ble strøket, ikke bare erstatte det"
    )
    assert "ingen utslippsfaktor" in tekst or "uten at noen utslippsfaktor må" in tekst
