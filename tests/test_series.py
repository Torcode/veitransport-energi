"""Den publiserbare statistikken skal være intern konsistent og korrekt merket."""
from __future__ import annotations

import pandas as pd
import pytest

from veitransport_energi.checks import group_sum_check
from veitransport_energi.series import COLUMNS, build_historical_statistics

GYLDIGE_STATUSER = {"observert", "konstruert", "estimert"}


@pytest.fixture(scope="module")
def hs():
    return build_historical_statistics()


@pytest.fixture(scope="module")
def gsum():
    return group_sum_check()


def test_skjema_og_obligatoriske_felt(hs):
    assert list(hs.columns) == COLUMNS
    for kol in ("serie_id", "gruppe", "variabel", "enhet", "frekvens", "periode", "kilde"):
        assert hs[kol].astype(str).str.strip().ne("").all(), f"tomme verdier i {kol}"
    assert hs["verdi"].notna().all()


def test_alle_rader_har_gyldig_status(hs):
    ugyldige = set(hs["status"].unique()) - GYLDIGE_STATUSER
    assert not ugyldige, f"ukjente statusverdier: {ugyldige}"


def test_ingen_framtidsrettede_storrelser_i_dette_laget(hs):
    """Begrepsdisiplin: scenarioer og framskrivinger hører til fase 5."""
    assert "scenarioforutsatt" not in set(hs["status"])
    assert "prognostisert" not in set(hs["status"])


def test_energiserien_er_merket_estimert_ikke_observert(hs):
    """Energi er beregnet med faktorer utenfor kilden og skal aldri stå som observert."""
    e = hs[hs["serie_id"].str.startswith("energi_")]
    assert len(e) > 0
    assert (e["status"] == "estimert").all()
    assert e["brudd"].str.contains("bio").all(), "forbeholdet om bioinnblanding mangler"


def test_bruddene_er_markert_der_de_finnes(hs):
    """2020-bruddet i autodiesel og hybridbruddet i kjørelengdene skal være synlige."""
    ad = hs[(hs["serie_id"] == "salg_autodiesel") & (hs["periode"] == "2020M01")]
    assert ad["brudd"].str.contains("innsamlingskorreksjon").all()
    hyb = hs[(hs["serie_id"] == "kjorelengde") & (hs["drivlinje"].str.startswith("hybrid"))
             & (hs["periode"] == "2015")]
    assert hyb["brudd"].str.contains("til og med 2015").all()


def test_gruppesummen_stemmer_med_restposten(gsum):
    """Med restposten «uspesifisert» skal drivlinjene summere eksakt til kildens total."""
    assert gsum["avvik_pct"].abs().max() < 1e-9, "gruppesummen stemmer ikke eksakt"


def test_restposten_er_liten_men_synlig(gsum):
    """Restposten skal være dokumentert liten — ellers er avgrensningen feil."""
    assert gsum["restpost_pct"].max() < 1.0, "restposten er for stor til å publiseres uforklart"
    varebiler = gsum[gsum["gruppe"] == "varebiler"]
    assert varebiler["restpost_pct"].max() > 0.1, (
        "testen forutsetter at restposten faktisk finnes for varebiler i tidlige år"
    )


def test_begge_kjoretoygrupper_er_med(hs):
    for gruppe in ("personbiler", "varebiler"):
        d = hs[hs["gruppe"] == gruppe]
        assert {"bestand", "kjorelengde"} <= set(d["serie_id"]), f"{gruppe} mangler serier"


def test_salgsseriene_har_segmentmerking(hs):
    s = hs[hs["serie_id"].str.startswith("salg_")]
    assert s["segment"].astype(str).str.strip().ne("").all(), "salgsserier uten segmentmerking"


def test_autodiesel_starter_2010_og_dieselsum_stopper_2019(hs):
    """Skjøtereglene D-0002/D-0003 skal være synlige i de publiserte seriene."""
    ad = hs[hs["serie_id"] == "salg_autodiesel"]["periode"]
    ds = hs[hs["serie_id"] == "salg_dieselsum"]["periode"]
    assert ad.min() == "2010M01"
    assert ds.max() == "2019M12"


def test_periodene_er_konsistente_med_frekvensen(hs):
    m = hs[hs["frekvens"] == "M"]["periode"]
    a = hs[hs["frekvens"] == "A"]["periode"]
    assert m.str.match(r"^\d{4}M\d{2}$").all()
    assert a.str.match(r"^\d{4}$").all()


def test_artefaktet_pa_disk_er_i_takt(hs):
    import os
    path = os.path.join(os.path.dirname(__file__), "..", "artifacts", "historical_statistics.csv")
    assert os.path.exists(path), "artefaktet mangler — kjør python -m veitransport_energi.artifacts"
    lagret = pd.read_csv(path, dtype=str, keep_default_na=False)
    assert len(lagret) == len(hs)
    assert list(lagret.columns) == COLUMNS
