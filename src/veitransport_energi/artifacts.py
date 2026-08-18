"""Bygging av versjonerte resultatartefakter.

Prosjektet skal ha én maskinlesbar sannhet som README, beslutningsflate,
rådgivernotat og metodenote alle leser fra — ingen hovedtall skrevet manuelt to
steder. Denne modulen skriver artefaktene og et manifest som binder dem til
datavintage, kodeversjon og git-commit.

Bruk:
    python -m veitransport_energi.artifacts
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

import pandas as pd

from . import __version__
from .assumptions import assumption_register
from .checks import control_tables
from .series import build_historical_statistics
from .stockflow import inflow_by_drivetrain

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ARTIFACTS = os.path.join(ROOT, "artifacts")
VINTAGE = os.path.join(ROOT, "data", "vintage.json")


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=10)
        return out.stdout if out.returncode == 0 else None
    except OSError:
        return None


def _git_state() -> dict[str, str]:
    """Commit artefaktene ble bygget fra, og om treet var endret da.

    Artefaktene bygges normalt før commit, så `git_commit` peker på forelderen til
    den commiten som til slutt inneholder dem. Uten `arbeidstre` ville det tallet
    sett ut som en eksakt binding det ikke er.
    """
    commit = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain")
    if commit is None:
        return {"git_commit": "ukjent", "arbeidstre": "ukjent"}
    return {
        "git_commit": commit.strip(),
        "arbeidstre": "rent" if status is not None and not status.strip() else "endret",
    }


def build_all() -> dict:
    os.makedirs(ARTIFACTS, exist_ok=True)
    written: dict[str, pd.DataFrame] = {
        "historical_statistics.csv": build_historical_statistics(),
        "inflow_by_drivetrain.csv": inflow_by_drivetrain(),
        "assumption_register.csv": assumption_register(),
    }
    for navn, df in control_tables().items():
        written[navn] = df

    for navn, df in written.items():
        df.to_csv(os.path.join(ARTIFACTS, navn), index=False)

    with open(VINTAGE, encoding="utf-8") as f:
        vintage = json.load(f)

    manifest = {
        "built_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **_git_state(),
        "code_version": __version__,
        "python": sys.version.split()[0],
        "data_vintage": {
            navn: {"table_id": v["table_id"], "source_updated": v["source_updated"],
                   "last_period": v["last_period"], "sha256_extract": v["sha256_extract"]}
            for navn, v in vintage["tables"].items()
        },
        "artifacts": {
            navn: {"rows": int(len(df)),
                   "sha256": _sha256(os.path.join(ARTIFACTS, navn))}
            for navn, df in written.items()
        },
        "merknad": (
            "Artefaktene inneholder kun observerte, konstruerte og estimerte størrelser. "
            "Framskrivinger og scenarioer hører til fase 5 og finnes ikke her. "
            "git_commit er treets tilstand da artefaktene ble bygget; er arbeidstre "
            "'endret', ble de bygget før commit, og den endelige commiten er en etterkommer."
        ),
    }
    with open(os.path.join(ARTIFACTS, "release_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    return manifest


def main() -> None:
    m = build_all()
    for navn, info in m["artifacts"].items():
        print(f"OK  {navn}: {info['rows']} rader")
    print(f"Manifest: artifacts/release_manifest.json (commit {m['git_commit'][:8]}, "
          f"kode {m['code_version']})")


if __name__ == "__main__":
    main()
