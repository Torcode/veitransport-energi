"""Antakelsesregister: hver parameter som ikke er observert, med kilde og spenn.

Registeret er en av prosjektets leveranser, ikke en intern hjelpefil. Enhver
størrelse modellen bruker uten å ha observert den, skal stå her med verdi,
enhet, gyldighet, kilde, status og usikkerhetsspenn — slik at en leser kan se
nøyaktig hvilke antakelser et resultat hviler på, og hvor de kommer fra.

Statusverdier:
    eksternt_anslag   — hentet fra navngitt ekstern kilde
    brukerantakelse   — satt av prosjektet uten ekstern kilde, med begrunnelse
    estimert          — beregnet fra prosjektets egne data
"""
from __future__ import annotations

import pandas as pd

COLUMNS = [
    "parameter_id", "variabel", "gjelder", "verdi", "enhet", "gyldighet",
    "status", "kilde", "usikkerhet_lav", "usikkerhet_hoy", "begrunnelse", "kjent_svakhet",
]

ASSUMPTIONS: list[dict] = [
    {
        "parameter_id": "UF_PHEV",
        "variabel": "utility factor — andel av ladbare hybriders kjørelengde på forbrenningsmotor",
        "gjelder": "personbiler og varebiler, ladbar hybrid",
        "verdi": 0.45,
        "enhet": "andel (0-1)",
        "gyldighet": "2016-",
        "status": "eksternt_anslag",
        "kilde": (
            "TØI-rapport 1492/2016 (Figenbaum & Kolbenstvedt): norske ladbare hybrider "
            "kjøres gjennomsnittlig 55 prosent i elmodus, selvrapportert, N=2 065 PHEV-eiere, "
            "undersøkelse mars 2016. Forbrenningsandelen er komplementet, 45 prosent"
        ),
        "usikkerhet_lav": 0.40,
        "usikkerhet_hoy": 0.75,
        "begrunnelse": (
            "Sentralverdien følger den eneste norske primærkilden. Spennet er bevisst "
            "asymmetrisk oppover: kilden er selvrapportert, ni år gammel, og EUs OBFCM-data "
            "for 2021-registrerte ladbare hybrider viser reelt CO2-utslipp 3,5 ganger over "
            "typegodkjenning, noe som tilsier vesentlig lavere elandel enn selvrapportert"
        ),
        "kjent_svakhet": (
            "Parameteren er IKKE identifiserbar fra prosjektets egne data: en variasjon på "
            "±20 prosent i antatt elbilintensitet gir implisert utility factor fra under 0 "
            "til over 1 (se control_utility_factor_identification.csv). Den må derfor komme "
            "utenfra og behandles som sensitivitetsparameter, aldri som kalibrert størrelse"
        ),
    },
    {
        "parameter_id": "INT_BEV_PERSONBIL",
        "variabel": "energiintensitet, elektrisk personbil",
        "gjelder": "personbiler, elektrisitet",
        "verdi": 0.20,
        "enhet": "kWh per km",
        "gyldighet": "ca. 2016-",
        "status": "eksternt_anslag",
        "kilde": (
            "NVE-notat om transport og kraftsystemet (Spilde/Skotland): 0,20 kWh/km for "
            "personbil, basert på måledata"
        ),
        "usikkerhet_lav": 0.18,
        "usikkerhet_hoy": 0.24,
        "begrunnelse": (
            "Prosjektets egen kalibrering — energibalansens elpost delt på observert "
            "kjørelengde — gir 0,21 kWh/km for hele elflåten ved utility factor 0,5, altså "
            "uavhengig samsvar med NVEs måling"
        ),
        "kjent_svakhet": (
            "Notatet er fra omkring 2016-2017 og omtaler ikke ladetap. Flåten er siden blitt "
            "tyngre, og faktisk forbruk per km kan ha steget"
        ),
    },
    {
        "parameter_id": "INT_BEV_VAREBIL",
        "variabel": "energiintensitet, elektrisk varebil",
        "gjelder": "varebiler, elektrisitet",
        "verdi": 0.25,
        "enhet": "kWh per km",
        "gyldighet": "ca. 2016-",
        "status": "eksternt_anslag",
        "kilde": "NVE-notat om transport og kraftsystemet (Spilde/Skotland): 0,25 kWh/km for varebil",
        "usikkerhet_lav": 0.22,
        "usikkerhet_hoy": 0.32,
        "begrunnelse": "Samme kilde som personbil; forholdet mellom gruppene er kildens eget",
        "kjent_svakhet": (
            "Som personbil. I tillegg er varebilflåtens elektrifisering ung, så måledata "
            "bygger på få kjøretøy"
        ),
    },
]


def assumption_register() -> pd.DataFrame:
    df = pd.DataFrame(ASSUMPTIONS, columns=COLUMNS)
    if df["parameter_id"].duplicated().any():
        raise ValueError("parameter_id må være unik i antakelsesregisteret")
    return df


def get(parameter_id: str) -> dict:
    """Hent én antakelse. Feiler høyt på ukjent id, slik at parametre ikke oppstår stille."""
    df = assumption_register()
    treff = df[df["parameter_id"] == parameter_id]
    if treff.empty:
        raise KeyError(f"ukjent parameter '{parameter_id}'; kjente: {list(df['parameter_id'])}")
    return treff.iloc[0].to_dict()
