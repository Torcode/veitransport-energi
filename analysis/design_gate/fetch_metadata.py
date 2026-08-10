"""Fase 0: Hent metadata for identifiserte SSB-tabeller via PxWebAPI v2-beta.

Kjøres én gang i designfasen. Alle svar caches til api_cache/ og alle
API-kall logges til request_log.csv (tidspunkt, URL, status, bytes).
"""
import json
import time
import urllib.request
import urllib.parse
import csv
import os
from datetime import datetime, timezone

BASE = "https://data.ssb.no/api/pxwebapi/v2-beta"
CACHE = os.path.join(os.path.dirname(__file__), "api_cache")
LOG = os.path.join(os.path.dirname(__file__), "request_log.csv")
TABLES = ["03687", "11174", "13585", "09654", "14020", "07849", "12576", "12577"]

os.makedirs(CACHE, exist_ok=True)


def log_request(url, status, nbytes):
    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp_utc", "url", "http_status", "bytes"])
        w.writerow([datetime.now(timezone.utc).isoformat(timespec="seconds"), url, status, nbytes])


def get(url, cache_name):
    path = os.path.join(CACHE, cache_name)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    req = urllib.request.Request(url, headers={"User-Agent": "design-gate-fase0 (kontakt: repo-eier)"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            log_request(url, r.status, len(raw))
    except urllib.error.HTTPError as e:
        body = e.read()[:400].decode("utf-8", "replace")
        log_request(url, e.code, len(body))
        raise RuntimeError(f"HTTP {e.code} for {url}: {body}")
    data = json.loads(raw)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    time.sleep(1.6)  # respekter API-ets ratebegrensning
    return data


def summarize(tid, meta):
    print("=" * 100)
    print(f"TABELL {tid}: {meta.get('label', '')}")
    print(f"  oppdatert: {meta.get('updated')}  kilde: {meta.get('source')}")
    for note in meta.get("note", []) or []:
        print(f"  NOTE(tabell): {note[:600]}")
    dims = meta.get("id", [])
    sizes = meta.get("size", [])
    for d, s in zip(dims, sizes):
        dim = meta["dimension"][d]
        cat = dim.get("category", {})
        codes = list(cat.get("index", {}))
        labels = cat.get("label", {})
        unit = cat.get("unit", None)
        elim = dim.get("extension", {}).get("elimination", None)
        print(f"  DIM {d} ({dim.get('label','')}), n={s}, elimination={elim}")
        if d == "Tid":
            print(f"    Tid: {codes[0]} ... {codes[-1]} (n={len(codes)})")
        elif s <= 45:
            for c in codes:
                u = f" [unit: {unit[c]['base']}]" if unit and c in unit else ""
                print(f"    {c}: {labels.get(c, '')}{u}")
        else:
            print(f"    (n={s}; første 8): " + "; ".join(f"{c}={labels.get(c,'')}" for c in codes[:8]))
        for nkey, ntxt in (dim.get("note") and {"dimnote": dim["note"]} or {}).items():
            for t in ntxt:
                print(f"    NOTE(dim {d}): {t[:500]}")
        # noter per kategori (verdinoter)
        ext = dim.get("extension", {})
        cnotes = ext.get("categoryNote") or {}
        for code, txts in list(cnotes.items())[:12]:
            for t in (txts if isinstance(txts, list) else [txts]):
                print(f"    NOTE({d}={code}): {t[:400]}")


if __name__ == "__main__":
    for tid in TABLES:
        meta = get(f"{BASE}/tables/{tid}/metadata?lang=no", f"{tid}_metadata.json")
        summarize(tid, meta)
    # Søk etter energibalansen (mulig valideringskilde for elektrisitet i veitransport)
    for q, name in [("energibalanse", "sok_energibalanse.json"), ("energibruk transport", "sok_energibruk_transport.json")]:
        res = get(f"{BASE}/tables?lang=no&query={urllib.parse.quote(q)}&pageSize=20", name)
        print("=" * 100)
        print(f"SØK: {q}")
        for t in res.get("tables", []):
            print(f"  {t.get('id')}: {t.get('label','')[:110]}  [{t.get('firstPeriod','')}–{t.get('lastPeriod','')}]  discontinued={t.get('discontinued')}")
