"""Klient for SSBs PxWebAPI v2-beta.

Designprinsipper (jf. docs/decision_log.md D-0013):
- alle dimensjoner angis eksplisitt med valueCodes (API-et krever det),
- alle kall logges maskinelt (tidspunkt, URL, status, bytes),
- alle svar caches som filer, slik at bygg og tester kan kjøres uten nettverk,
- moderat tempo mot API-et (pause mellom kall).
"""
from __future__ import annotations

import csv
import itertools
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import pandas as pd

BASE = "https://data.ssb.no/api/pxwebapi/v2-beta"
USER_AGENT = "veitransport-energi (github.com/Torcode/veitransport-energi)"
PAUSE_SECONDS = 1.8


class PxWebError(RuntimeError):
    """Feil fra PxWebAPI (HTTP-feil eller uventet svar)."""


def _log_request(log_path: str, url: str, status: int, nbytes: int) -> None:
    new = not os.path.exists(log_path)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp_utc", "url", "http_status", "bytes"])
        w.writerow([datetime.now(timezone.utc).isoformat(timespec="seconds"), url, status, nbytes])


def fetch_json(url: str, cache_path: str, log_path: str, refresh: bool = False) -> dict:
    """Hent JSON fra API-et med filcache og forespørselslogg."""
    if os.path.exists(cache_path) and not refresh:
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            raw = r.read()
            _log_request(log_path, url, r.status, len(raw))
    except urllib.error.HTTPError as e:
        body = e.read()[:500].decode("utf-8", "replace")
        _log_request(log_path, url, e.code, len(body))
        raise PxWebError(f"HTTP {e.code} for {url}: {body}") from e
    data = json.loads(raw)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    time.sleep(PAUSE_SECONDS)
    return data


def metadata_url(table_id: str) -> str:
    return f"{BASE}/tables/{table_id}/metadata?lang=no"


def data_url(table_id: str, value_codes: dict[str, list[str]]) -> str:
    parts: list[tuple[str, str]] = [("lang", "no"), ("outputFormat", "json-stat2")]
    for dim, codes in value_codes.items():
        parts.append((f"valueCodes[{dim}]", ",".join(codes)))
    return f"{BASE}/tables/{table_id}/data?" + urllib.parse.urlencode(parts, safe=",*()")


def jsonstat_to_df(ds: dict) -> pd.DataFrame:
    """Tidy DataFrame fra JSON-stat2: én rad per celle med kode, etikett, verdi og status."""
    dims = ds["id"]
    sizes = ds["size"]
    cats: dict[str, tuple[list[str], dict]] = {}
    for d in dims:
        idx = ds["dimension"][d]["category"]["index"]
        codes = sorted(idx, key=idx.get) if isinstance(idx, dict) else list(idx)
        labels = ds["dimension"][d]["category"].get("label", {})
        cats[d] = (codes, labels)
    values = ds["value"]
    status = ds.get("status") or {}
    rows = []
    for flat, combo in enumerate(itertools.product(*[range(s) for s in sizes])):
        row: dict[str, object] = {}
        for d, pos in zip(dims, combo, strict=True):
            codes, labels = cats[d]
            row[d] = codes[pos]
            row[d + "_label"] = labels.get(codes[pos], codes[pos])
        row["value"] = values[flat]
        row["status"] = status.get(str(flat), "")
        rows.append(row)
    return pd.DataFrame(rows)


def contents_units(meta: dict) -> dict[str, str]:
    """Måleenhet per ContentsCode fra metadata (brukes av kontraktene)."""
    dim = meta["dimension"].get("ContentsCode", {})
    unit = dim.get("category", {}).get("unit", {}) or {}
    return {code: (info or {}).get("base", "") for code, info in unit.items()}
