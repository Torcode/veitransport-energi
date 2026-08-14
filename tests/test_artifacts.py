"""Manifestet skal binde artefaktene, ikke bare beskrive dem.

Prosjektet lover én maskinlesbar sannhet som README, beslutningsflate,
rådgivernotat og metodenote leser fra. Løftet er bare verdt noe hvis manifestet
og filene ikke kan komme fra hverandre stille: et artefakt bygget om uten at
manifestet følger med, ville gitt lesere en sjekksum som ikke lenger gjelder.
"""
from __future__ import annotations

import hashlib
import json
import os

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ARTIFACTS = os.path.join(ROOT, "artifacts")
MANIFEST = os.path.join(ARTIFACTS, "release_manifest.json")


@pytest.fixture(scope="module")
def manifest():
    assert os.path.exists(MANIFEST), "release_manifest.json mangler — kjør artifacts-modulen"
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def test_manifestet_har_de_sporingsfeltene_det_lover(manifest):
    for felt in ("built_utc", "git_commit", "arbeidstre", "code_version", "data_vintage",
                 "artifacts", "merknad"):
        assert felt in manifest, f"manifestet mangler {felt}"
    assert manifest["arbeidstre"] in ("rent", "endret", "ukjent")


def test_sjekksummene_stemmer_med_filene_pa_disk(manifest):
    """Kjernetesten: en artefakt kan ikke bygges om uten at manifestet følger med."""
    for navn, info in manifest["artifacts"].items():
        sti = os.path.join(ARTIFACTS, navn)
        assert os.path.exists(sti), f"manifestet viser til {navn}, som ikke finnes"
        assert _sha256(sti) == info["sha256"], (
            f"{navn} er endret etter at manifestet ble skrevet — kjør artifacts-modulen"
        )


def test_ingen_artefakt_ligger_utenfor_manifestet():
    """Filer i artifacts/ uten manifestoppføring er upubliserte hovedtall."""
    with open(MANIFEST, encoding="utf-8") as f:
        oppfort = set(json.load(f)["artifacts"])
    pa_disk = {n for n in os.listdir(ARTIFACTS) if n.endswith(".csv")}
    assert pa_disk == oppfort, f"utenfor manifestet: {sorted(pa_disk - oppfort)}"


def test_hvert_artefakt_har_rader_og_datavintage(manifest):
    assert manifest["artifacts"], "manifestet er tomt"
    for navn, info in manifest["artifacts"].items():
        assert info["rows"] > 0, f"{navn} er tomt — en tom tabell er ikke et resultat"
    for navn, v in manifest["data_vintage"].items():
        for felt in ("table_id", "source_updated", "last_period", "sha256_extract"):
            assert str(v.get(felt, "")).strip(), f"{navn} mangler {felt} i datavintage"


def test_figursporet_peker_paa_manifestet_som_ligger_her():
    """Figurene skal ikke kunne bli stående på et grunnlag som er skiftet ut.

    Kontrollen finnes i CI som en gjenbygging i R, men den er også ren
    filsammenligning — og bør derfor feile lokalt, før en push, uten at R er
    installert.

    Første utgave av figursporet førte også manifestets commit og
    byggetidspunkt. Begge endrer seg av seg selv hver gang artefaktene bygges
    ved en ny HEAD, så kontrollen ble rød uten at figurene var feil, og den
    røde CI-en fulgte med inn på main. Sporet inneholder nå bare størrelser som
    er stabile gitt samme grunnlag.
    """
    spor_sti = os.path.join(ROOT, "figurer", "figurspor.json")
    if not os.path.exists(spor_sti):
        pytest.skip("figurer/figurspor.json mangler — kjør Rscript R/bygg_figurer.R")
    with open(spor_sti, encoding="utf-8") as f:
        spor = json.load(f)

    flyktige = {"artefakt_commit", "artefakter_bygget", "bygget_utc", "git_commit"}
    assert not flyktige & set(spor), (
        f"figursporet inneholder felt som endrer seg av seg selv: {flyktige & set(spor)}"
    )
    assert spor["manifest_sha256"] == _sha256(MANIFEST), (
        "figurene er bygget fra et annet manifest enn det som ligger her — "
        "kjør python -m veitransport_energi.artifacts og deretter Rscript R/bygg_figurer.R"
    )
    for navn, info in spor["figurer"].items():
        assert os.path.exists(os.path.join(ROOT, "figurer", navn)), f"{navn} mangler"
        assert info["tittel"].strip(), f"{navn} mangler tittel i sporet"
