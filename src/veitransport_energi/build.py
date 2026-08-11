"""Byggkommandoen for datalaget: hent, kontroller, skriv uttrekk og vintage.

Bruk:
    python -m veitransport_energi.build            # hent (med cache) og bygg alt
    python -m veitransport_energi.build --offline  # bygg kun fra eksisterende cache
    python -m veitransport_energi.build --refresh  # tving nye API-kall

Skriver:
    data/raw/<name>_data.json, <table>_metadata.json   (rå API-svar, cache)
    data/raw/request_log.csv                           (alle API-kall)
    data/extracts/<name>.csv                           (tidy uttrekk)
    data/vintage.json                                  (vintage-manifest med sjekksummer)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

from . import pxweb
from .contracts import check_extract
from .tables import SPECS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW = os.path.join(ROOT, "data", "raw")
EXTRACTS = os.path.join(ROOT, "data", "extracts")
LOG = os.path.join(RAW, "request_log.csv")


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10
        )
        return out.stdout.strip() if out.returncode == 0 else "ukjent"
    except OSError:
        return "ukjent"


def build(offline: bool = False, refresh: bool = False) -> dict:
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(EXTRACTS, exist_ok=True)
    manifest: dict = {
        "built_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": _git_commit(),
        "python": sys.version.split()[0],
        "tables": {},
    }
    reports = []
    for spec in SPECS:
        meta_path = os.path.join(RAW, f"{spec.table_id}_metadata.json")
        data_path = os.path.join(RAW, f"{spec.name}_data.json")
        if offline:
            if not (os.path.exists(meta_path) and os.path.exists(data_path)):
                raise FileNotFoundError(f"--offline, men cache mangler for {spec.name}")
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
            with open(data_path, encoding="utf-8") as f:
                ds = json.load(f)
        else:
            meta = pxweb.fetch_json(pxweb.metadata_url(spec.table_id), meta_path, LOG, refresh=refresh)
            url = pxweb.data_url(spec.table_id, spec.value_codes)
            ds = pxweb.fetch_json(url, data_path, LOG, refresh=refresh)
        df = pxweb.jsonstat_to_df(ds)
        report = check_extract(df, spec, units_from_meta=pxweb.contents_units(meta))
        reports.append(report)
        out_csv = os.path.join(EXTRACTS, f"{spec.name}.csv")
        df.to_csv(out_csv, index=False)
        tids = sorted(df["Tid"].astype(str).unique())
        manifest["tables"][spec.name] = {
            "table_id": spec.table_id,
            "source_updated": meta.get("updated"),
            "first_period": tids[0],
            "last_period": tids[-1],
            "rows": report["rows"],
            "sha256_raw": _sha256(data_path),
            "sha256_extract": _sha256(out_csv),
        }
        print(f"OK  {spec.name}: {report['rows']} rader, {tids[0]}-{tids[-1]}")
    with open(os.path.join(ROOT, "data", "vintage.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    commit8 = manifest["git_commit"][:8]
    print(f"Vintage skrevet: data/vintage.json ({len(reports)} tabeller, commit {commit8})")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description="Bygg datalaget for veitransport-energi")
    ap.add_argument("--offline", action="store_true", help="bruk kun eksisterende cache")
    ap.add_argument("--refresh", action="store_true", help="tving nye API-kall")
    args = ap.parse_args()
    build(offline=args.offline, refresh=args.refresh)


if __name__ == "__main__":
    main()
