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

**Brudd i aldersdefinisjonen mellom 2023 og 2024.** Måler man hvor stor del av
fire årganger førstegangsregistreringer som gjenfinnes i gruppen «under 4 år»,
ligger forholdet mellom 0,58 og 0,72 fra 2008 til 2023 — og hopper så til 0,92
i 2024 og 0,94 i 2025. Totalsummen over aldersgruppene stemmer fortsatt med
bestandstabellen innenfor 1,3 prosent, så det er ikke bestanden som har endret
seg, men hvordan alder er beregnet. Bruddet er ikke omtalt i tabellens noter.

Kohortsporing over denne grensen sammenligner derfor to ulike definisjoner.
`survival_curve` utelater som standard alle overganger som krysser bruddet;
uten den avgrensningen ville de to siste årgangene ha framstått som en reell
nedgang i overlevelse, når de i virkeligheten måler en definisjonsendring.
"""
from __future__ import annotations

import pandas as pd

from .datasets import read_extract

AGE_ORDER = ["Under 4 år", "4 - 7 år", "8 - 11 år", "12 - 15 år", "16 - 20 år", "Over 20 år"]
AGE_CODES = {"02": "Under 4 år", "03": "4 - 7 år", "04": "8 - 11 år",
             "05": "12 - 15 år", "06": "16 - 20 år", "07": "Over 20 år"}
GROUP_VARIABLE = {"personbiler": "Personbiler", "varebiler": "Varebiler"}
STEP_YEARS = 4

# Siste startår hvis overgangen ikke skal krysse definisjonsbruddet: en overgang
# fra år t leser bestand i t+4, så t må være 2019 for å slutte i 2023.
LAST_UNBROKEN_START = "2019"
DEFINITION_BREAK_YEAR = "2024"


def age_distribution(gruppe: str) -> pd.DataFrame:
    """Aldersfordelt bestand per år (index: år, kolonner: aldersgruppe)."""
    if gruppe not in GROUP_VARIABLE:
        raise KeyError(f"ukjent gruppe '{gruppe}'; kjente: {list(GROUP_VARIABLE)}")
    df = read_extract("age_08581")
    d = df[df["ContentsCode"] == GROUP_VARIABLE[gruppe]].copy()
    d["aldersgruppe"] = d["Alder"].map(AGE_CODES)
    p = d.pivot_table(index="Tid", columns="aldersgruppe", values="value", aggfunc="sum")
    return p[[c for c in AGE_ORDER if c in p.columns]].sort_index()


def definition_break_check(gruppe: str) -> pd.DataFrame:
    """Andelen av fire årganger førstegangsregistreringer som gjenfinnes i «under 4 år».

    Et stabilt forhold betyr at aldersgruppen fanger den samme delen av
    registreringene år for år. Et hopp betyr at definisjonen er endret.
    """
    from .datasets import read_extract

    p = age_distribution(gruppe)
    variabel = "Personbiler" if gruppe == "personbiler" else "VareCampBiler"
    fr = read_extract("firstreg_14020").copy()
    fr["aar"] = fr["Tid"].astype(str).str[:4]
    reg = fr[fr["ContentsCode"] == variabel].groupby("aar")["value"].sum()
    rows = []
    for aar in p.index:
        fire = [str(y) for y in range(int(aar) - 3, int(aar) + 1)]
        if not all(y in reg.index for y in fire):
            continue
        sum_reg = sum(reg[y] for y in fire)
        rows.append({
            "gruppe": gruppe, "periode": aar,
            "bestand_under_4_aar": p.loc[aar, "Under 4 år"],
            "sum_forstegangsreg_4_aar": sum_reg,
            "dekningsforhold": p.loc[aar, "Under 4 år"] / sum_reg if sum_reg else float("nan"),
            "etter_brudd": aar >= DEFINITION_BREAK_YEAR,
        })
    df = pd.DataFrame(rows)
    df["merknad"] = (
        "forholdet hopper mellom 2023 og 2024 uten at tabellens noter omtaler det; "
        "aldersdefinisjonen er lagt om, og kohortsporing over grensen er ugyldig"
    )
    return df


def cohort_transitions(gruppe: str, include_break: bool = False) -> pd.DataFrame:
    """Fireårs overgangsrater mellom aldersgrupper, per startår.

    include_break tar med overganger som krysser definisjonsbruddet. Den finnes
    bare for å kunne vise hva bruddet gjør; produksjonskode skal ikke sette den.
    """
    p = age_distribution(gruppe)
    rows = []
    for aar in p.index:
        senere = str(int(aar) + STEP_YEARS)
        if senere not in p.index:
            continue
        if not include_break and aar > LAST_UNBROKEN_START:
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


def survival_curve(gruppe: str, include_break: bool = False) -> pd.DataFrame:
    """Gjennomsnittlig overgangsrate per aldersovergang, med spredning over årene.

    Utelater som standard overganger som krysser definisjonsbruddet i 2024.
    """
    t = cohort_transitions(gruppe, include_break=include_break)
    agg = (t.groupby(["gruppe", "fra_alder", "til_alder"])["overgangsrate"]
           .agg(["mean", "std", "min", "max", "count"]).reset_index())
    agg = agg.rename(columns={"mean": "rate_snitt", "std": "rate_std",
                              "min": "rate_min", "max": "rate_maks", "count": "antall_aar"})
    agg["stabil"] = agg["rate_std"] < 0.10
    agg["merknad"] = (
        "fireårs overgangsrate ved kohortsporing; måler netto endring per "
        "aldersgruppe, ikke ren overlevelse — bruktimport løfter den yngste "
        "overgangen over 1. Ingen drivstoffdeling i kilden. Overganger som "
        f"krysser definisjonsbruddet i {DEFINITION_BREAK_YEAR} er utelatt"
    )
    # bevar aldersrekkefølgen framfor alfabetisk sortering
    agg["_ord"] = agg["fra_alder"].map({a: i for i, a in enumerate(AGE_ORDER)})
    return agg.sort_values("_ord").drop(columns="_ord").reset_index(drop=True)
