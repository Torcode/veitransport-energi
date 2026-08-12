"""Hvor stor del av drivstoffetterspørselen prosjektets estimand faktisk dekker.

Fase 5 skal framskrive etterspørselen etter bensin, autodiesel og elektrisitet.
Modellen dekker person- og varebiler. Spørsmålet det da er umulig å komme utenom:
hvor mye av hver energibærer *er* person- og varebiler?

Svaret er sterkt asymmetrisk, og asymmetrien avgjør hva en framskriving kan
påstå. Den beregnes her framfor å antas, fordi den bærer avgrensningen i
scenariodesignet.

## Hva tallene her er, og hva de ikke er

Størrelsen som beregnes, er **andel av kjørte kilometer**, ikke andel av
drivstoffvolum. Skillet er ikke pedantisk. Et vogntog bruker flere ganger så mye
diesel per kilometer som en personbil, så tunge kjøretøys andel av
*dieselvolumet* er vesentlig større enn deres andel av *kilometerne*. Tallene her
er derfor en øvre grense for hvor stor del av dieselen prosjektet dekker, ikke et
anslag på den.

For bensin spiller forskjellen liten rolle, siden nesten alt bensinforbruk er
personbiler uansett. For diesel er den avgjørende.

Kilden har ingen drivstoffdeling per kjøretøytype som gir volum, bare kilometer.
Å gjøre om til volum ville krevd energiintensitet per kjøretøygruppe, som
prosjektet ikke observerer — se `reconstruction_intensity_bounds.csv`, der den
kalibrerte intensiteten gjelder hele veitransporten under ett.
"""
from __future__ import annotations

import pandas as pd

from .datasets import read_extract
from .series import DRIVLINJER, GROUPS

ALLE_KJORETOY = "0"
DEKKEDE_ENERGIBAERERE = ("bensin", "diesel", "elektrisitet")


def estimand_coverage() -> pd.DataFrame:
    """Andel av kjørte kilometer per energibærer som ligger innenfor estimandet.

    Én rad per år og energibærer, med personbiler og varebiler hver for seg og
    samlet. `andel_utenfor_pct` er resten: busser, lastebiler, trekkbiler,
    drosjer, campingbiler og øvrige grupper prosjektet ikke modellerer.
    """
    km = read_extract("km_12577")
    d = km[km["ContentsCode"] == "Kjorelengde"].copy()

    rows = []
    for baerer in DEKKEDE_ENERGIBAERERE:
        koder = DRIVLINJER[baerer]
        f = d[d["DrivstoffType"].isin(koder)]
        total = f[f["Kjoretoytype"] == ALLE_KJORETOY].groupby("Tid")["value"].sum()
        per_gruppe = {
            gruppe: f[f["Kjoretoytype"].isin(spec["km_koder"])].groupby("Tid")["value"].sum()
            for gruppe, spec in GROUPS.items()
        }
        for tid in sorted(total.index):
            alle = total[tid]
            if not alle:
                continue
            pb = per_gruppe["personbiler"].get(tid, 0.0)
            vb = per_gruppe["varebiler"].get(tid, 0.0)
            rows.append({
                "kontroll": "estimandets_dekning_kjorelengde",
                "energibaerer": baerer,
                "periode": tid,
                "km_alle_kjoretoy": alle,
                "km_personbiler": pb,
                "km_varebiler": vb,
                "andel_personbiler_pct": pb / alle * 100,
                "andel_varebiler_pct": vb / alle * 100,
                "andel_innenfor_estimandet_pct": (pb + vb) / alle * 100,
                "andel_utenfor_pct": (alle - pb - vb) / alle * 100,
                "status": "observert",
            })
    df = pd.DataFrame(rows)
    df["merknad"] = (
        "andel av kjørte kilometer, ikke av drivstoffvolum; tunge kjøretøy bruker "
        "flere ganger mer per kilometer, så andelen av dieselvolumet som ligger "
        "innenfor estimandet, er lavere enn tallet her. Kilden oppgir ikke volum "
        "per kjøretøytype"
    )
    return df
