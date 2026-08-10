"""Fase 0: Hent små dataprøver fra SSB PxWebAPI v2-beta for designportens empiriske tester.

Alle kall logges til request_log.csv og caches. Uttrekkene lagres som tidy CSV i extracts/.
"""
import json
import time
import urllib.request
import urllib.parse
import csv
import os
import itertools
from datetime import datetime, timezone

import pandas as pd

BASE = "https://data.ssb.no/api/pxwebapi/v2-beta"
HERE = os.path.dirname(__file__)
CACHE = os.path.join(HERE, "api_cache")
EXTRACTS = os.path.join(HERE, "extracts")
LOG = os.path.join(HERE, "request_log.csv")
os.makedirs(CACHE, exist_ok=True)
os.makedirs(EXTRACTS, exist_ok=True)


def log_request(url, status, nbytes):
    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp_utc", "url", "http_status", "bytes"])
        w.writerow([datetime.now(timezone.utc).isoformat(timespec="seconds"), url, status, nbytes])


def get_json(url, cache_name):
    path = os.path.join(CACHE, cache_name)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    req = urllib.request.Request(url, headers={"User-Agent": "design-gate-fase0"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            raw = r.read()
            log_request(url, r.status, len(raw))
    except urllib.error.HTTPError as e:
        body = e.read()[:500].decode("utf-8", "replace")
        log_request(url, e.code, len(body))
        raise RuntimeError(f"HTTP {e.code} for {url}: {body}")
    data = json.loads(raw)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    time.sleep(1.8)
    return data


def data_url(table, value_codes):
    parts = [("lang", "no"), ("outputFormat", "json-stat2")]
    for dim, codes in value_codes.items():
        parts.append((f"valueCodes[{dim}]", ",".join(codes)))
    return f"{BASE}/tables/{table}/data?" + urllib.parse.urlencode(parts, safe=",*()")


def jsonstat_to_df(ds):
    """Tidy DataFrame fra JSON-stat2: én rad per celle, med kode, etikett, verdi, status."""
    dims = ds["id"]
    sizes = ds["size"]
    cats = {}
    for d in dims:
        idx = ds["dimension"][d]["category"]["index"]
        if isinstance(idx, dict):
            codes = sorted(idx, key=idx.get)
        else:
            codes = list(idx)
        labels = ds["dimension"][d]["category"].get("label", {})
        cats[d] = (codes, labels)
    values = ds["value"]
    status = ds.get("status") or {}
    rows = []
    for flat, combo in enumerate(itertools.product(*[range(s) for s in sizes])):
        row = {}
        for d, pos in zip(dims, combo):
            codes, labels = cats[d]
            row[d] = codes[pos]
            row[d + "_label"] = labels.get(codes[pos], codes[pos])
        row["value"] = values[flat]
        row["status"] = status.get(str(flat), "")
        rows.append(row)
    return pd.DataFrame(rows)


def fetch_table(table, value_codes, outname):
    url = data_url(table, value_codes)
    ds = get_json(url, f"data_{outname}.json")
    df = jsonstat_to_df(ds)
    out = os.path.join(EXTRACTS, f"{outname}.csv")
    df.to_csv(out, index=False)
    n_missing = df["value"].isna().sum()
    print(f"{table} -> {outname}: {len(df)} celler, {n_missing} manglende. Lagret {out}")
    return df


if __name__ == "__main__":
    # 1) Salg 03687: hele landet, alle kjøpegrupper; totalen, bilbensin, diesel
    fetch_table("03687", {
        "Region": ["0"], "Kjopegrupper": ["00"],
        "PetroleumProd": ["00", "03", "04"],
        "ContentsCode": ["Petroleum"], "Tid": ["*"],
    }, "sales_03687")

    # 2) Salg 11174: totalen, bilbensin, anleggsdiesel, autodiesel
    fetch_table("11174", {
        "Region": ["0"], "Kjopegrupper": ["00"],
        "PetroleumProd": ["00", "03", "04a", "04b"],
        "ContentsCode": ["Petroleum"], "Tid": ["*"],
    }, "sales_11174")

    # 3) Salg 13585: alle tre måltall (totalt, petroleum inkl. iblanda bio, reint bio)
    fetch_table("13585", {
        "Kjopegrupper": ["00"],
        "Produkter": ["00", "01", "02a", "02b"],
        "ContentsCode": ["Total", "Petroleum", "Biodrivstoff"], "Tid": ["*"],
    }, "sales_13585")

    # 4) Førstegangsregistrerte 14020: personbiler og varebiler, alle drivstoff, nye+bruktimport
    fetch_table("14020", {
        "TypeRegistrering": ["N", "B"], "DrivstoffType": ["19", "20", "21", "6"],
        "ContentsCode": ["Personbiler", "VareCampBiler"], "Tid": ["*"],
    }, "firstreg_14020")

    # 5) Bestand 07849: hele landet, personbiler og varebiler etter drivstoff.
    #    KjoringensArt har elimination=True; prøv å utelate for å få totalen.
    try:
        fetch_table("07849", {
            "Region": ["0"], "DrivstoffType": ["1", "2", "3", "4", "5", "6"],
            "ContentsCode": ["Personbil1", "Varebil4"], "Tid": ["*"],
        }, "stock_07849")
        print("07849: KjoringensArt utelatt -> eliminert (totalen).")
    except RuntimeError as e:
        print(f"07849 uten KjoringensArt feilet ({e}); prøver med alle 7 arter for aggregering.")
        fetch_table("07849", {
            "Region": ["0"], "KjoringensArt": ["1", "2", "3", "4", "5", "6", "7"],
            "DrivstoffType": ["1", "2", "3", "4", "5", "6"],
            "ContentsCode": ["Personbil1", "Varebil4"], "Tid": ["*"],
        }, "stock_07849_arter")

    # 6) Kjørelengder 12577: personbiler i alt + varebiler, alle 12 drivstoffkoder, begge måltall
    fetch_table("12577", {
        "Kjoretoytype": ["0", "15", "20", "29", "30", "00"],
        "DrivstoffType": ["0", "1", "2", "18", "14", "15", "16", "17", "3", "4", "13", "7"],
        "ContentsCode": ["Kjorelengde", "GjsnittKjorelengde"], "Tid": ["*"],
    }, "km_12577")

    # 7) Drivstoffpriser 09654: hele serien (liten)
    fetch_table("09654", {
        "PetroleumProd": ["031", "035"], "ContentsCode": ["Priser"], "Tid": ["*"],
    }, "prices_09654")

    # 8) Energibalansen 11561: metadata for å avklare om veitransport x elektrisitet finnes
    meta = get_json(f"{BASE}/tables/11561/metadata?lang=no", "11561_metadata.json")
    print("=" * 90)
    print(f"11561: {meta.get('label','')}")
    for d, s in zip(meta.get("id", []), meta.get("size", [])):
        dim = meta["dimension"][d]
        print(f"  DIM {d} ({dim.get('label','')}), n={s}")
        codes = list(dim.get("category", {}).get("index", {}))
        labels = dim.get("category", {}).get("label", {})
        hits = [c for c in codes if any(k in labels.get(c, "").lower()
                for k in ("veitransport", "vegtransport", "elektrisitet", "transport i alt"))]
        for c in hits[:15]:
            print(f"    {c}: {labels.get(c,'')}")

    # 9) Tabellsøk: finnes en bestandstabell med ladbar/ikke-ladbar hybrid?
    for q, name in [("registrerte kj%C3%B8ret%C3%B8y drivstofftype", "sok_bestand_drivstoff.json"),
                    ("personbiler drivstofftype", "sok_personbiler_drivstoff.json")]:
        res = get_json(f"{BASE}/tables?lang=no&query={q}&pageSize=20", name)
        print("=" * 90)
        print(f"SØK: {urllib.parse.unquote(q)}")
        for t in res.get("tables", []):
            print(f"  {t.get('id')}: {t.get('label','')[:100]}  [{t.get('firstPeriod','')}–{t.get('lastPeriod','')}]")
