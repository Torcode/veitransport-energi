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


def test_modellens_parametre_star_i_registeret():
    """Ingen modellstørrelse skal leve i koden uten å være ført i registeret."""
    from veitransport_energi.cohort import FITTED_PARAMS

    for drivlinje, p in FITTED_PARAMS.items():
        etikett = "EL" if drivlinje == "elektrisitet" else "IKKEEL"
        assert get(f"SURV_SKALA_{etikett}")["verdi"] == p.scale
        assert get(f"SURV_FORM_{etikett}")["verdi"] == p.shape
        assert get("SURV_IMPORTALDER")["verdi"] == p.import_age


def test_overlevelsesspennet_er_hentet_fra_stabilitetstabellen():
    """Spennene skal være beregnet, ikke skrevet inn for hånd.

    Registeret oppgir usikkerheten for overlevelsesparametrene som spredningen
    ved reestimering på rullerende vinduer. Her leses den tilbake fra tabellen
    som produserer den; avviker de, er ett av stedene håndredigert.
    """
    path = os.path.join(os.path.dirname(__file__), "..", "artifacts",
                        "control_survival_parameter_stability.csv")
    assert os.path.exists(path), "stabilitetstabellen mangler — kjør artifacts-modulen"
    tab = pd.read_csv(path)
    for drivlinje, etikett in (("elektrisitet", "EL"), ("ikke_elektrisk", "IKKEEL")):
        d = tab[tab["drivlinje"] == drivlinje]
        assert not d.empty, f"stabilitetstabellen mangler {drivlinje}"
        for stor, kolonne in (("SKALA", "weibull_scale"), ("FORM", "weibull_shape")):
            a = get(f"SURV_{stor}_{etikett}")
            assert a["usikkerhet_lav"] == pytest.approx(d[kolonne].min()), (
                f"SURV_{stor}_{etikett}: nedre spenn stemmer ikke med tabellen"
            )
            assert a["usikkerhet_hoy"] == pytest.approx(d[kolonne].max()), (
                f"SURV_{stor}_{etikett}: øvre spenn stemmer ikke med tabellen"
            )


def test_profilen_er_smalere_enn_vindusspredningen():
    """Den smale SSE-profilen skal ikke kunne bli registerets usikkerhetsspenn.

    Profilen innenfor ett estimeringsvindu er skarp fordi residualene er
    seriekorrelerte, ikke fordi parameteren er godt bestemt. Testen låser at
    registeret oppgir det bredere, ærlige spennet.
    """
    path = os.path.join(os.path.dirname(__file__), "..", "artifacts",
                        "control_survival_parameter_stability.csv")
    tab = pd.read_csv(path)
    for drivlinje, etikett in (("elektrisitet", "EL"), ("ikke_elektrisk", "IKKEEL")):
        d = tab[tab["drivlinje"] == drivlinje]
        profil = (d["profil_skala_hoy"] - d["profil_skala_lav"]).max()
        vindu = d["weibull_scale"].max() - d["weibull_scale"].min()
        assert profil < vindu, f"{drivlinje}: profil {profil} skal være smalere enn {vindu}"
        a = get(f"SURV_SKALA_{etikett}")
        assert a["usikkerhet_hoy"] - a["usikkerhet_lav"] == pytest.approx(vindu)
