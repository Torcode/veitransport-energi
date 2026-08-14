"""Kjørelengde per kjøretøy — og hvorfor den ikke kan modelleres som mekanisme.

Scenariodesignet (D-0032) slo fast at kjørelengde per kjøretøy ikke kan antas
konstant: den har falt systematisk for fossile biler og steget for elbiler. Det
nærliggende neste steget var å gjøre den til en strukturell størrelse — bilene
kjøres mindre fordi parken eldes — og la kohortmodellens egen aldersbane drive
den. Denne modulen er kontrollen som avviste det.

## Hvorfor kontrollen var nødvendig

I nivå ser sammenhengen overbevisende ut: kjørelengde per ikke-elektrisk
personbil korrelerer omkring −0,98 med modellert gjennomsnittsalder. Men
gjennomsnittsalderen stiger nesten lineært med kalendertiden i det observerte
vinduet, og de to korrelerer over 0,98 med hverandre. En regresjon på alder og
en regresjon på år er da nesten samme regresjon.

Førstedifferanser skiller dem. Faller kjørelengden *fordi* parken eldes, skal år
med sterk aldring gi sterkere fall enn år med svak. Det gjør de ikke:
korrelasjonen i differanser er tilnærmet null.

## Hva som følger

Mekanismen er ikke identifisert av disse dataene. En modell bygget på
nivåsammenhengen ville ekstrapolert selvsikkert til 2035 på en relasjon som ikke
lar seg skille fra en ren trend — og feilen ville vært usynlig i tilpasningen,
siden nivåsammenhengen er utmerket. Kjørelengde per kjøretøy føres derfor som
scenarioforutsetning med spenn, ikke som estimert relasjon, og tabellen her er
begrunnelsen.

Det er også et argument for at et fall ikke kan fortsette vilkårlig langt: et
kjøretøy som nærmer seg null kilometer, blir avregistrert, og da er det
nettoavgangen som fanger det. En ubegrenset nedadgående trend ville telt samme
uttreden to ganger.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .cohort import FITTED_PARAMS, load_flows, simulate
from .series import build_historical_statistics

MINSTE_BESTAND = 5_000  # under dette er km per kjøretøy for støyete til å tolke


def mileage_per_vehicle(gruppe: str = "personbiler") -> pd.DataFrame:
    """Observert kjørelengde per kjøretøy per drivlinje og år.

    Både fin drivlinjedeling (bensin, diesel, elektrisitet) og den grove
    todelingen modellen bruker, slik at tallet kan sammenlignes med
    kohortmodellens aldersbane.
    """
    h = build_historical_statistics()
    h = h[h["gruppe"] == gruppe]
    km = h[h["variabel"] == "kjorelengde_total"].pivot_table(
        index="periode", columns="drivlinje", values="verdi", aggfunc="sum")
    best = h[h["variabel"] == "bestand_3112"].pivot_table(
        index="periode", columns="drivlinje", values="verdi", aggfunc="sum")

    grov_km = pd.DataFrame({
        "elektrisitet": km.get("elektrisitet"),
        "ikke_elektrisk": km.drop(columns=[c for c in ("elektrisitet",) if c in km], errors="ignore")
                            .sum(axis=1),
    })
    grov_best = pd.DataFrame({
        "elektrisitet": best.get("elektrisitet"),
        "ikke_elektrisk": best.drop(columns=[c for c in ("elektrisitet",) if c in best],
                                    errors="ignore").sum(axis=1),
    })

    rows = []
    for oppdeling, k, b in (("fin", km, best), ("grov", grov_km, grov_best)):
        felles = k.index.intersection(b.index)
        for drivlinje in k.columns:
            if drivlinje not in b.columns:
                continue
            for tid in sorted(felles):
                bestand = b.loc[tid, drivlinje]
                if not bestand or pd.isna(bestand) or bestand < MINSTE_BESTAND:
                    continue
                rows.append({
                    "gruppe": gruppe, "oppdeling": oppdeling, "drivlinje": drivlinje,
                    "periode": tid,
                    "kjorelengde_mill_km": k.loc[tid, drivlinje],
                    "bestand_3112": bestand,
                    "km_per_kjoretoy": k.loc[tid, drivlinje] * 1e6 / bestand,
                    "status": "konstruert fra observerte data",
                })
    df = pd.DataFrame(rows)
    df["merknad"] = (
        "kjørelengde gjelder hele året, bestanden er talt 31.12; for en drivlinje "
        "i rask vekst gjør det nevneren for stor og forholdstallet for lavt"
    )
    return df


def mileage_identification(gruppe: str = "personbiler") -> pd.DataFrame:
    """Kan fallet i kjørelengde per kjøretøy tilskrives at parken eldes?

    Sammenligner nivå- og differansesammenhengen mellom kjørelengde per kjøretøy
    og kohortmodellens gjennomsnittsalder. Kolonnen `identifisert` er sann bare
    dersom differansesammenhengen er sterk nok til å bære en strukturell
    tolkning — den er det ikke, og det er poenget med tabellen.
    """
    km = mileage_per_vehicle(gruppe)
    km = km[km["oppdeling"] == "grov"].pivot_table(
        index="periode", columns="drivlinje", values="km_per_kjoretoy")

    flows = load_flows(gruppe)
    alder = pd.DataFrame({
        drivlinje: simulate(flows, p, drivlinje, "2008", "2025")
                     .set_index("periode")["gjsn_alder"]
        for drivlinje, p in FITTED_PARAMS.items()
    })

    rows = []
    for drivlinje in FITTED_PARAMS:
        if drivlinje not in km.columns:
            continue
        d = pd.DataFrame({"km": km[drivlinje], "alder": alder[drivlinje]}).dropna()
        d["aar"] = d.index.astype(int)
        if len(d) < 8:
            continue
        diff = d.diff().dropna()
        rows.append({
            "kontroll": "identifikasjon_kjorelengde_per_kjoretoy",
            "gruppe": gruppe, "drivlinje": drivlinje,
            "aar_fra": d.index.min(), "aar_til": d.index.max(), "antall_aar": len(d),
            "korr_niva_km_mot_alder": float(np.corrcoef(d["alder"], d["km"])[0, 1]),
            "korr_niva_km_mot_tid": float(np.corrcoef(d["aar"], d["km"])[0, 1]),
            "korr_alder_mot_tid": float(np.corrcoef(d["alder"], d["aar"])[0, 1]),
            "korr_differanse_km_mot_alder": float(np.corrcoef(diff["alder"], diff["km"])[0, 1]),
            "endring_pct_per_aar": float(
                (np.exp(np.polyfit(d["aar"], np.log(d["km"]), 1)[0]) - 1) * 100),
            "status": "konstruert fra observerte data",
        })
    df = pd.DataFrame(rows)
    df["identifisert"] = df["korr_differanse_km_mot_alder"].abs() > 0.5
    df["merknad"] = (
        "nivåsammenhengen mellom kjørelengde per kjøretøy og flåtealder kan ikke "
        "skilles fra en ren tidstrend: alder og kalenderår er nær kollineære i "
        "vinduet, og sammenhengen forsvinner i førstedifferanser. Størrelsen "
        "føres derfor som scenarioforutsetning med spenn, ikke som estimert "
        "relasjon (D-0034)"
    )
    return df
