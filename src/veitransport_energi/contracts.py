"""Datakontrakter for uttrekkene.

Kontraktene skal feile høyt og tidlig. De kontrollerer det som kan kontrolleres
maskinelt uten skjønn: nøkkelentydighet, enheter mot metadata, tidsaksens
kontinuitet, prikkekonsistens og ikke-negativitet for volumstørrelser.
"""
from __future__ import annotations

import re

import pandas as pd

from .tables import TableSpec

MONTH_RE = re.compile(r"^\d{4}M(0[1-9]|1[0-2])$")
YEAR_RE = re.compile(r"^\d{4}$")

# Statistikkvariabler der negative verdier er faglig mulige (ingen per i dag).
ALLOW_NEGATIVE: set[tuple[str, str]] = set()


class ContractError(AssertionError):
    """Bruddet på en datakontrakt, med alle funn samlet."""

    def __init__(self, spec_name: str, problems: list[str]):
        self.spec_name = spec_name
        self.problems = problems
        super().__init__(f"[{spec_name}] " + " | ".join(problems))


def _expected_periods(tids: list[str], freq: str) -> list[str]:
    """Komplett periodeliste fra første til siste observerte periode."""
    if freq == "A":
        first, last = int(tids[0]), int(tids[-1])
        return [str(y) for y in range(first, last + 1)]
    y0, m0 = int(tids[0][:4]), int(tids[0][5:7])
    y1, m1 = int(tids[-1][:4]), int(tids[-1][5:7])
    out = []
    y, m = y0, m0
    while (y, m) <= (y1, m1):
        out.append(f"{y}M{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def check_extract(df: pd.DataFrame, spec: TableSpec, units_from_meta: dict[str, str] | None = None) -> dict:
    """Kjør alle kontrakter for ett uttrekk. Returnerer rapport, kaster ContractError ved brudd."""
    problems: list[str] = []

    # 1) Nødvendige kolonner
    needed = {"Tid", "value", "status", *spec.key_dims}
    missing = needed - set(df.columns)
    if missing:
        raise ContractError(spec.name, [f"mangler kolonner: {sorted(missing)}"])

    # 2) Tidsformat
    tid_re = YEAR_RE if spec.freq == "A" else MONTH_RE
    bad_tid = df.loc[~df["Tid"].astype(str).str.match(tid_re), "Tid"].unique()
    if len(bad_tid):
        problems.append(f"ugyldig tidsformat: {list(bad_tid)[:5]}")

    # 3) Nøkkelentydighet
    key_cols = [*spec.key_dims, "Tid"]
    dups = df.duplicated(subset=key_cols)
    if dups.any():
        problems.append(f"{int(dups.sum())} duplikatnøkler ({key_cols})")

    # 4) Tidsaksens kontinuitet (fullstendig kartesisk dekning per nøkkel)
    if not len(bad_tid):
        tids = sorted(df["Tid"].astype(str).unique())
        expected = _expected_periods(tids, spec.freq)
        holes = set(expected) - set(tids)
        if holes:
            problems.append(f"hull i tidsaksen: {sorted(holes)[:6]}")
        counts = df.groupby("Tid").size()
        if counts.nunique() > 1:
            problems.append(f"ujevn celledekning per periode: {sorted(counts.unique())}")

    # 5) Prikkekonsistens: statuskode uten verdi, verdi uten statuskode
    prikket = df["status"].fillna("").astype(str).str.strip().isin({"..", ":", "."})
    has_val = df["value"].notna()
    inconsistent = int((prikket & has_val).sum())
    if inconsistent:
        problems.append(f"{inconsistent} celler har både prikkekode og verdi")
    missing_unexplained = int((~prikket & ~has_val).sum())
    if missing_unexplained and not spec.allow_unexplained_missing:
        problems.append(f"{missing_unexplained} manglende verdier uten statuskode")

    # 6) Ikke-negativitet
    if "ContentsCode" in df.columns:
        for cc, grp in df.groupby("ContentsCode"):
            if (spec.name, str(cc)) in ALLOW_NEGATIVE:
                continue
            neg = int((grp["value"] < 0).sum())
            if neg:
                problems.append(f"{neg} negative verdier for {cc}")
    else:
        neg = int((df["value"] < 0).sum())
        if neg:
            problems.append(f"{neg} negative verdier")

    # 7) Enheter mot metadata
    if units_from_meta is not None:
        for cc, expected_unit in spec.expected_units.items():
            got = units_from_meta.get(cc, "")
            if got and got != expected_unit:
                problems.append(f"enhet for {cc}: metadata sier '{got}', spesifikasjonen '{expected_unit}'")

    if problems:
        raise ContractError(spec.name, problems)
    return {
        "spec": spec.name,
        "rows": int(len(df)),
        "periods": int(df["Tid"].nunique()),
        "missing_with_status": int((prikket & ~has_val).sum()),
    }
