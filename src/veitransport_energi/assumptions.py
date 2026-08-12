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
    {
        "parameter_id": "SURV_SKALA_IKKEEL",
        "variabel": "Weibull-skala i kohortmodellens overlevelseskurve, ikke-elektriske",
        "gjelder": "personbiler, ikke-elektrisk drivlinje",
        "verdi": 20.2,
        "enhet": "år",
        "gyldighet": "estimert på 2009-2015, validert på 2016-2025",
        "status": "estimert",
        "kilde": (
            "Prosjektets egen estimering: rutenettsøk som minimerer relativt kvadratavvik "
            "mot observert bestand i SSB-tabell 07849, gitt observert tilgang i 14020 "
            "(veitransport_energi.cohort.fit_survival)"
        ),
        "usikkerhet_lav": 19.7,
        "usikkerhet_hoy": 20.5,
        "begrunnelse": (
            "Spennet er reestimering på fire rullerende sjuårsvinduer 2009-2025, se "
            "control_survival_parameter_stability.csv. Skalaen flytter seg 0,8 år over "
            "vinduene, altså fire prosent — nivået er godt identifisert av bestandsnivåene"
        ),
        "kjent_svakhet": (
            "Kurven måler netto overlevelse i det norske registeret, ikke fysisk levetid: "
            "eksport og avregistrering ligger inne i samme ledd, og kilden skiller dem ikke. "
            "SSE-profilen innenfor ett vindu er langt smalere (20,1-20,4) fordi residualene "
            "er sterkt seriekorrelerte; den skal ikke leses som usikkerhet"
        ),
    },
    {
        "parameter_id": "SURV_FORM_IKKEEL",
        "variabel": "Weibull-form i kohortmodellens overlevelseskurve, ikke-elektriske",
        "gjelder": "personbiler, ikke-elektrisk drivlinje",
        "verdi": 2.4,
        "enhet": "dimensjonsløs",
        "gyldighet": "estimert på 2009-2015, validert på 2016-2025",
        "status": "estimert",
        "kilde": "Som SURV_SKALA_IKKEEL; formen estimeres i samme rutenettsøk",
        "usikkerhet_lav": 1.9,
        "usikkerhet_hoy": 2.9,
        "begrunnelse": (
            "Samme reestimering over rullerende vinduer. Formen flytter seg fra 1,9 til 2,9, "
            "altså 40 prosent — vesentlig dårligere identifisert enn skalaen"
        ),
        "kjent_svakhet": (
            "Formen bestemmer hvor brått avgangen inntreffer, og den er ikke pinnet av data. "
            "Bestandsnivåene identifiserer i hovedsak levetidsnivået; hvordan avgangen "
            "fordeler seg over alder, må derfor bæres som sensitivitetsparameter i fase 5"
        ),
    },
    {
        "parameter_id": "SURV_SKALA_EL",
        "variabel": "Weibull-skala i kohortmodellens overlevelseskurve, elektriske",
        "gjelder": "personbiler, elektrisitet",
        "verdi": 11.8,
        "enhet": "år",
        "gyldighet": "estimert på 2009-2015, validert på 2016-2025",
        "status": "estimert",
        "kilde": "Som SURV_SKALA_IKKEEL, med elektrisk bestand og tilgang",
        "usikkerhet_lav": 11.1,
        "usikkerhet_hoy": 12.3,
        "begrunnelse": (
            "Reestimering på fire rullerende vinduer gir 11,1-12,3. Verdien reproduserer "
            "observert elbestand med 0,03-0,92 prosents avvik over ti år som ikke inngikk "
            "i estimeringen"
        ),
        "kjent_svakhet": (
            "Den alvorligste begrensningen i modellen. Bare sju prosent av elbestanden i 2025 "
            "er over åtte år, så kurven er belagt med data bare i sin begynnelse. Ved de "
            "estimerte parametrene er S(20) tilnærmet null — det er funksjonsformen som "
            "løper videre forbi observasjonene, ikke et anslag på elbilers levetid. Verdien "
            "er dessuten netto: eksport av tidlige elbiler ligger inne i avgangen. Spennet "
            "over vinduene måler stabilitet innenfor observerte aldre og dekker ikke halen"
        ),
    },
    {
        "parameter_id": "SURV_FORM_EL",
        "variabel": "Weibull-form i kohortmodellens overlevelseskurve, elektriske",
        "gjelder": "personbiler, elektrisitet",
        "verdi": 4.4,
        "enhet": "dimensjonsløs",
        "gyldighet": "estimert på 2009-2015, validert på 2016-2025",
        "status": "estimert",
        "kilde": "Som SURV_SKALA_EL; formen estimeres i samme rutenettsøk",
        "usikkerhet_lav": 3.4,
        "usikkerhet_hoy": 5.3,
        "begrunnelse": (
            "Reestimering over rullerende vinduer gir 3,4-5,3, det bredeste spennet av de "
            "fire overlevelsesparametrene"
        ),
        "kjent_svakhet": (
            "Som SURV_FORM_IKKEEL, men strammere: en høy formparameter presser avgangen "
            "sammen rundt skalaen, og det er nettopp i det aldersområdet elbilflåten ennå "
            "ikke har vært. Kombinasjonen av høy form og lav skala er derfor det leddet i "
            "modellen som en framskriving er mest følsom for"
        ),
    },
    {
        "parameter_id": "SURV_IMPORTALDER",
        "variabel": "antatt alder på bruktimporterte kjøretøy ved innførsel",
        "gjelder": "personbiler og varebiler, alle drivlinjer",
        "verdi": 3,
        "enhet": "år",
        "gyldighet": "hele modellperioden",
        "status": "brukerantakelse",
        "kilde": (
            "Ingen. SSB-tabell 14020 oppgir antall bruktimporterte førstegangsregistreringer, "
            "men ikke kjøretøyenes alder, og prosjektet har ikke funnet en primærkilde som "
            "gjør det"
        ),
        "usikkerhet_lav": 2,
        "usikkerhet_hoy": 5,
        "begrunnelse": (
            "Alderen må settes for at bruktimporten skal kunne legges i en årskohort. Spennet "
            "er satt der modellens treff på 2025 holder seg innenfor samme størrelsesorden "
            "som modellfeilen for øvrig: avviket for ikke-elektriske går fra -1,17 prosent "
            "ved to år til -3,61 prosent ved fem år, mot -2,03 prosent ved den valgte verdien"
        ),
        "kjent_svakhet": (
            "Antakelsen er ikke belagt, bare avgrenset. Følsomhetstallene over holder "
            "overlevelsesparametrene fast på verdier som selv er estimert under samme "
            "antakelse, så en felles reestimering ville dempet utslaget noe. Å hente aldersfordelt "
            "bruktimport fra Statens vegvesen ville gjort parameteren observert framfor antatt"
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
