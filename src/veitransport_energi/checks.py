"""Kontrolltabeller til den publiserbare statistikken.

Kontrolltabellene er en del av leveransen, ikke bare av testene: en leser skal
kunne se hvordan seriene henger sammen med kildene og med hverandre, uten å
kjøre koden selv.

Tabellene faller i tre grupper:

Avstemminger mot kildene
    gruppesum (publiserte drivlinjer mot kildens totalserie), bestand mot
    aktivitet (koblingen fra D-0020) og energiavstemming (salgsenergi mot
    energibalansens veitransportpost).

Rekonstruerte størrelser
    nettoavgang som residual i bestand-strøm-identiteten, og kalibrert
    energiintensitet med sitt spenn.

Validering og identifikasjon
    backcast av rate-modellen, kohortmodellens tidsdelte validering,
    overlevelseskurven fra aldersdata, definisjonsbruddet i aldersgruppene,
    parameterstabiliteten i overlevelseskurven, og påvisningen av at utility
    factor ikke lar seg identifisere fra prosjektets egne data.

Avgrensning
    hvor stor del av hver energibærers kjørelengde som ligger innenfor
    estimandet — grunnlaget for hva fase 5 kan framskrive og hva den ikke kan.
"""
from __future__ import annotations

import pandas as pd

from .cohort import FITTED_PARAMS, parameter_stability
from .cohort import load_flows as cohort_flows
from .cohort import simulate as cohort_simulate
from .coverage import estimand_coverage
from .datasets import read_extract
from .diagnostics import energy_reconciliation, utility_factor_identification
from .linkage import stock_vs_activity
from .reconstruction import calibrated_intensity, net_retirement
from .series import DRIVLINJER, GROUPS
from .stockflow import backcast
from .survival import definition_break_check, survival_curve


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
        "reconstruction_net_retirement.csv": net_retirement(),
        "reconstruction_intensity_bounds.csv": calibrated_intensity(),
        "control_utility_factor_identification.csv": utility_factor_identification(),
        "validation_backcast.csv": pd.concat([
            backcast("personbiler", "grov", [str(a) for a in range(2010, 2016)], "2015", "2025"),
            backcast("varebiler", "grov", [str(a) for a in range(2010, 2016)], "2015", "2025"),
            backcast("personbiler", "fin", ["2020", "2021", "2022"], "2022", "2025"),
            backcast("varebiler", "fin", ["2020", "2021", "2022"], "2022", "2025"),
        ], ignore_index=True),
        "survival_curve.csv": pd.concat(
            [survival_curve("personbiler"), survival_curve("varebiler")], ignore_index=True),
        "validation_cohort_model.csv": pd.concat([
            cohort_simulate(cohort_flows("personbiler"), p, dl, "2008", "2025").assign(
                gruppe="personbiler", weibull_scale=p.scale, weibull_shape=p.shape,
                avvik_pct=lambda d: (d["modellert"] - d["observert"]) / d["observert"] * 100)
            for dl, p in FITTED_PARAMS.items()
        ], ignore_index=True),
        "control_age_definition_break.csv": pd.concat(
            [definition_break_check("personbiler"), definition_break_check("varebiler")],
            ignore_index=True),
        "control_survival_parameter_stability.csv": parameter_stability("personbiler"),
        "control_estimand_coverage.csv": estimand_coverage(),
    }
