"""Overlevelseskurver for kjøretøyparken, estimert ved kohortsporing.

Designporten satte betingelsen for å gå fra en konstant avgangsrate til en
kohort- eller overlevelsesmodell (M3): den mer avanserte metoden skal bare tas
inn dersom aldersdataene faktisk identifiserer overlevelse bedre enn
residualraten. Denne modulen leverer grunnlaget for den avgjørelsen.

Metoden er kohortsporing i aldersgrupper. Aldersgruppene i SSB-tabell 08581 er
fire år brede, så en gruppe i år t skal svare til neste gruppe i år t+4. Andelen
som gjenfinnes, er en fireårs overlevelsesrate.

To forbehold følger av datagrunnlaget, og begge er vesentlige:

Raten for den yngste overgangen ligger over 1 — omkring 1,39 for personbiler.
Det er ikke overlevelse over hundre prosent, men netto tilvekst: bruktimporterte
biler er typisk noen år gamle og lander i aldersgruppen «4–7 år» uten å ha vært
i «under 4 år» fire år tidligere. Kurven måler derfor netto endring per
aldersgruppe, ikke ren overlevelse, og navnet på størrelsen sier det.

Aldersdataene har ingen drivstoffdeling. Kurven gjelder hele person- eller
varebilparken under ett, og kan ikke uten videre brukes per drivlinje — en
elbilpark og en bensinbilpark med ulik aldersprofil vil ha ulik samlet avgang
selv med samme aldersspesifikke rater. Det er nettopp den mekanismen en
kohortmodell fanger, og en konstant rate ikke gjør.
"""
from __future__ import annotations

import pandas as pd

from .datasets import read_extract

AGE_ORDER = ["Under 4 år", "4 - 7 år", "8 - 11 år", "12 - 15 år", "16 - 20 år", "Over 20 år"]
AGE_CODES = {"02": "Under 4 år", "03": "4 - 7 år", "04": "8 - 11 år",
             "05": "12 - 15 år", "06": "16 - 20 år", "07": "Over 20 år"}
GROUP_VARIABLE = {"personbiler": "Personbiler", "varebiler": "Varebiler"}
STEP_YEARS = 4


def age_distribution(gruppe: str) -> pd.DataFrame:
    """Aldersfordelt bestand per år (index: år, kolonner: aldersgruppe)."""
    if gruppe not in GROUP_VARIABLE:
        raise KeyError(f"ukjent gruppe '{gruppe}'; kjente: {list(GROUP_VARIABLE)}")
    df = read_extract("age_08581")
    d = df[df["ContentsCode"] == GROUP_VARIABLE[gruppe]].copy()
    d["aldersgruppe"] = d["Alder"].map(AGE_CODES)
    p = d.pivot_table(index="Tid", columns="aldersgruppe", values="value", aggfunc="sum")
    return p[[c for c in AGE_ORDER if c in p.columns]].sort_index()


def cohort_transitions(gruppe: str) -> pd.DataFrame:
    """Fireårs overgangsrater mellom aldersgrupper, per startår."""
    p = age_distribution(gruppe)
    rows = []
    for aar in p.index:
        senere = str(int(aar) + STEP_YEARS)
        if senere not in p.index:
            continue
        for i in range(len(AGE_ORDER) - 1):
            fra, til = AGE_ORDER[i], AGE_ORDER[i + 1]
            if fra not in p.columns or til not in p.columns:
                continue
            a = p.loc[aar, fra]
            if not a:
                continue
            rows.append({
                "gruppe": gruppe, "startaar": aar, "sluttaar": senere,
                "fra_alder": fra, "til_alder": til,
                "bestand_start": a, "bestand_slutt": p.loc[senere, til],
                "overgangsrate": p.loc[senere, til] / a,
            })
    return pd.DataFrame(rows)


def survival_curve(gruppe: str) -> pd.DataFrame:
    """Gjennomsnittlig overgangsrate per aldersovergang, med spredning over årene."""
    t = cohort_transitions(gruppe)
    agg = (t.groupby(["gruppe", "fra_alder", "til_alder"])["overgangsrate"]
           .agg(["mean", "std", "min", "max", "count"]).reset_index())
    agg = agg.rename(columns={"mean": "rate_snitt", "std": "rate_std",
                              "min": "rate_min", "max": "rate_maks", "count": "antall_aar"})
    agg["stabil"] = agg["rate_std"] < 0.10
    agg["merknad"] = (
        "fireårs overgangsrate ved kohortsporing; måler netto endring per "
        "aldersgruppe, ikke ren overlevelse — bruktimport løfter den yngste "
        "overgangen over 1. Ingen drivstoffdeling i kilden"
    )
    # bevar aldersrekkefølgen framfor alfabetisk sortering
    agg["_ord"] = agg["fra_alder"].map({a: i for i, a in enumerate(AGE_ORDER)})
    return agg.sort_values("_ord").drop(columns="_ord").reset_index(drop=True)
