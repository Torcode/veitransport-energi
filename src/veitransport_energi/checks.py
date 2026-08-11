"""Kontrolltabeller til den publiserbare statistikken.

Kontrolltabellene er en del av leveransen, ikke bare av testene: en leser skal
kunne se hvordan seriene henger sammen med kildene og med hverandre, uten å
kjøre koden selv.

Tre kontroller:
    1. Gruppesum — publiserte drivlinjer skal summere til kildens totalserie.
    2. Bestand mot aktivitet — koblingen fra D-0020, år for år.
    3. Energiavstemming — salgsenergi mot energibalansens veitransportpost.
"""
from __future__ import annotations

import pandas as pd

from .datasets import read_extract
from .diagnostics import energy_reconciliation
from .linkage import stock_vs_activity
from .series import DRIVLINJER, GROUPS


def group_sum_check() -> pd.DataFrame:
    """Summen av publiserte drivlinjer mot kildens «alle typer drivstoff».

    Med restposten «uspesifisert» skal summen stemme eksakt. Kolonnen
    `restpost_pct` viser hvor stor del av totalen som ikke lot seg fordele på
    drivlinje fordi kilden undertrykker små kategorier.
    """
    km = read_extract("km_12577")
    tot = km[km["ContentsCode"] == "Kjorelengde"]
    publiserte = [k for koder in DRIVLINJER.values() for k in koder]
    rows = []
    for gruppe, spec in GROUPS.items():
        d = tot[tot["Kjoretoytype"].isin(spec["km_koder"])]
        sum_deler = d[d["DrivstoffType"].isin(publiserte)].groupby("Tid")["value"].sum()
        kildens_total = d[d["DrivstoffType"] == "0"].groupby("Tid")["value"].sum()
        for tid in sorted(kildens_total.index):
            a = kildens_total[tid]
            b = sum_deler.get(tid, 0.0)
            rest = a - b
            rows.append({"kontroll": "gruppesum_kjorelengde", "gruppe": gruppe, "periode": tid,
                         "kildens_total": a, "sum_publiserte_drivlinjer": b,
                         "restpost_uspesifisert": rest,
                         "restpost_pct": rest / a * 100 if a else float("nan"),
                         "sum_med_restpost": b + rest,
                         "avvik_pct": ((b + rest) - a) / a * 100 if a else float("nan")})
    return pd.DataFrame(rows)


def control_tables() -> dict[str, pd.DataFrame]:
    """Alle kontrolltabeller som skal følge med artefaktene."""
    sva = stock_vs_activity().rename(columns={"Tid": "periode"})
    sva.insert(0, "kontroll", "bestand_mot_aktivitet")
    rec = energy_reconciliation(
        read_extract("sales_11174"), read_extract("sales_13585"),
        read_extract("energybalance_11561_road"),
    ).reset_index().rename(columns={"aar": "periode"})
    rec.insert(0, "kontroll", "energiavstemming_salg_mot_energibalanse")
    return {
        "control_group_sums.csv": group_sum_check(),
        "control_stock_vs_activity.csv": sva,
        "control_energy_reconciliation.csv": rec,
    }
