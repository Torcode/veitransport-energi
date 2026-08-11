"""Maskingenerert kodebok for uttrekkene.

Kodeboken forklarer hver kode som faktisk forekommer i `data/extracts/`:
hvilken tabell og dimensjon den hører til, hva etiketten er, hvilken enhet
statistikkvariabelen har, og hvilke noter SSB har knyttet til koden.

Den utledes fra de cachede metadatasvarene, ikke skrevet for hånd. Dermed kan
den ikke komme i utakt med dataene: en test krever at hver kode i uttrekkene
har en rad her, og at ingen rad viser til en kode som ikke finnes i dataene.
"""
from __future__ import annotations

import json
import os

import pandas as pd

from .tables import SPECS, TableSpec

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW = os.path.join(ROOT, "data", "raw")
EXTRACTS = os.path.join(ROOT, "data", "extracts")
OUT = os.path.join(ROOT, "data", "metadata", "codebook.csv")

COLUMNS = [
    "table_id", "extract", "dimension", "dimension_label",
    "code", "code_label", "unit", "role", "note",
]


def _clean(text: object) -> str:
    """Én linje uten linjeskift, slik at CSV-en er lett å lese og diffe."""
    if text is None:
        return ""
    return " ".join(str(text).split())


def _table_note_rows(spec: TableSpec, meta: dict) -> list[dict]:
    """Tabellnotene fra SSB.

    Disse bærer de tyngste tolkningsforbeholdene — at «annet drivstoff» i
    bestandstabellen hovedsakelig er hybrider, at autodieseltall fra 2020 ikke
    er sammenlignbare bakover, at hybrider lå i bensin/diesel til og med 2015 —
    og hører derfor hjemme i kodeboken, ikke bare i rådataene.
    """
    rows: list[dict] = []
    for i, note in enumerate(meta.get("note", []) or [], start=1):
        rows.append({
            "table_id": spec.table_id, "extract": spec.name, "dimension": "(tabell)",
            "dimension_label": _clean(meta.get("label")), "code": f"note{i}",
            "code_label": "", "unit": "", "role": "tabellnote", "note": _clean(note),
        })
    return rows


def _dimension_rows(spec: TableSpec, meta: dict, used_codes: dict[str, set[str]]) -> list[dict]:
    rows: list[dict] = []
    for dim in meta.get("id", []):
        d = meta["dimension"][dim]
        cat = d.get("category", {})
        labels = cat.get("label", {}) or {}
        units = cat.get("unit", {}) or {}
        ext = d.get("extension", {}) or {}
        cat_notes = ext.get("categoryNote") or {}
        if dim == "Tid":
            role = "tid"
        elif dim == "ContentsCode":
            role = "statistikkvariabel"
        else:
            role = "klassifisering"
        codes = used_codes.get(dim, set())
        if dim == "Tid":
            # Tidsaksen dokumenteres som spenn, ikke som én rad per periode.
            if codes:
                lo, hi = min(codes), max(codes)
                rows.append({
                    "table_id": spec.table_id, "extract": spec.name, "dimension": dim,
                    "dimension_label": _clean(d.get("label")), "code": f"{lo}--{hi}",
                    "code_label": f"{len(codes)} perioder ({'måned' if spec.freq == 'M' else 'år'})",
                    "unit": "", "role": role, "note": _clean((d.get("note") or [""])[0]),
                })
            continue
        for code in sorted(codes):
            note = cat_notes.get(code)
            if isinstance(note, list):
                note = "; ".join(note)
            rows.append({
                "table_id": spec.table_id, "extract": spec.name, "dimension": dim,
                "dimension_label": _clean(d.get("label")),
                "code": code, "code_label": _clean(labels.get(code, "")),
                "unit": _clean((units.get(code) or {}).get("base", "")),
                "role": role, "note": _clean(note),
            })
    return rows


def build_codebook() -> pd.DataFrame:
    """Bygg kodeboken fra cachede metadata + kodene som forekommer i uttrekkene."""
    rows: list[dict] = []
    for spec in SPECS:
        meta_path = os.path.join(RAW, f"{spec.table_id}_metadata.json")
        extract_path = os.path.join(EXTRACTS, f"{spec.name}.csv")
        if not (os.path.exists(meta_path) and os.path.exists(extract_path)):
            raise FileNotFoundError(
                f"mangler grunnlag for {spec.name}; kjør `python -m veitransport_energi.build` først"
            )
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        df = pd.read_csv(extract_path, dtype=str)
        used = {dim: set(df[dim].dropna().unique()) for dim in meta.get("id", []) if dim in df.columns}
        rows.extend(_table_note_rows(spec, meta))
        rows.extend(_dimension_rows(spec, meta, used))
    return pd.DataFrame(rows, columns=COLUMNS)


def write_codebook() -> str:
    cb = build_codebook()
    cb.to_csv(OUT, index=False)
    return OUT


if __name__ == "__main__":
    path = write_codebook()
    cb = pd.read_csv(path)
    print(f"Kodebok skrevet: {os.path.relpath(path, ROOT)} — {len(cb)} rader, "
          f"{cb['extract'].nunique()} uttrekk, {cb['dimension'].nunique()} dimensjoner")
