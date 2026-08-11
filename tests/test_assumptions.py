"""Antakelsesregisteret skal være fullstendig, sporbart og ærlig om svakheter."""
from __future__ import annotations

import os

import pandas as pd
import pytest

from veitransport_energi.assumptions import COLUMNS, assumption_register, get
from veitransport_energi.diagnostics import utility_factor_identification

GYLDIGE_STATUSER = {"eksternt_anslag", "brukerantakelse", "estimert"}


@pytest.fixture(scope="module")
def reg():
    return assumption_register()


def test_skjema_og_unike_parametre(reg):
    assert list(reg.columns) == COLUMNS
    assert reg["parameter_id"].is_unique
    assert len(reg) > 0


def test_hver_antakelse_har_kilde_begrunnelse_og_svakhet(reg):
    for kol in ("kilde", "begrunnelse", "kjent_svakhet", "enhet", "gyldighet"):
        tomme = reg[reg[kol].astype(str).str.strip().eq("")]
        assert tomme.empty, f"antakelser uten {kol}: {list(tomme['parameter_id'])}"


def test_alle_statuser_er_gyldige(reg):
    assert set(reg["status"]) <= GYLDIGE_STATUSER


def test_usikkerhetsspennet_omslutter_verdien(reg):
    galt = reg[~((reg["usikkerhet_lav"] <= reg["verdi"]) & (reg["verdi"] <= reg["usikkerhet_hoy"]))]
    assert galt.empty, f"verdi utenfor eget spenn: {list(galt['parameter_id'])}"


def test_ukjent_parameter_feiler_hoyt():
    """Parametre skal ikke kunne oppstå stille utenfor registeret."""
    with pytest.raises(KeyError, match="ukjent parameter"):
        get("FINNES_IKKE")
    assert get("UF_PHEV")["status"] == "eksternt_anslag"


def test_utility_factor_er_ikke_identifiserbar_fra_egne_data():
    """Begrunnelsen for at parameteren er ekstern, ikke kalibrert.

    Spennet i implisert elandel når elbilintensiteten varierer innenfor sitt eget
    usikkerhetsintervall, skal være så bredt at residualen er uinformativ.
    """
    d = utility_factor_identification()
    siste = d[d["periode"] == d["periode"].max()]
    spenn = siste["implisert_elandel_hybrid"].max() - siste["implisert_elandel_hybrid"].min()
    assert spenn > 0.5, (
        f"testen forutsetter at residualen er uinformativ; observert spenn {spenn:.2f}"
    )
    assert siste["implisert_elandel_hybrid"].max() > 1.0, (
        "minst ett anslag skal være umulig (over 100 prosent), som viser at metoden ikke bærer"
    )


def test_uf_kilden_er_riktig_attribuert(reg):
    """Kilden er TØI 1492/2016, ikke Figenbaum & Weber 2018 — den inneholder ikke UF-tallet."""
    kilde = get("UF_PHEV")["kilde"]
    assert "1492/2016" in kilde
    assert "Kolbenstvedt" in kilde
    assert "selvrapportert" in kilde, "selvrapporteringen skal stå i kilden, ikke skjules"


def test_registeret_pa_disk_er_i_takt(reg):
    path = os.path.join(os.path.dirname(__file__), "..", "artifacts", "assumption_register.csv")
    assert os.path.exists(path), "assumption_register.csv mangler — kjør artifacts-modulen"
    lagret = pd.read_csv(path)
    assert list(lagret.columns) == COLUMNS
    assert len(lagret) == len(reg)
