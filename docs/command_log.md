# Kommando- og oppslagslogg, fase 0 (2026-08-10)

Alle SSB-API-kall er i tillegg maskinelt logget med tidsstempel, URL, HTTP-status og bytes i `analysis/design_gate/request_log.csv`; cache av alle svar ligger i `analysis/design_gate/api_cache/`. Loggen under er den operative kjørerekkefølgen.

## Skript og kommandoer (kjørt i angitt rekkefølge)

| # | Kommando/skript | Formål | Utfall |
|---|---|---|---|
| 1 | `mkdir -p …/docs …/data/metadata …/analysis/design_gate/api_cache` | Minimal lokal prosjektmappe for designporten | OK |
| 2 | `python3 -c "import pandas"` | Verifisere kjøremiljø | pandas 3.0.2 |
| 3 | `curl …/v2-beta/tables/13585/metadata?lang=no` | Teste API-tilgang fra miljøet | HTTP 200 |
| 4 | `python3 analysis/design_gate/fetch_metadata.py` | Metadata for 03687, 11174, 13585, 09654, 14020, 07849, 12576, 12577 + tabellsøk «energibalanse», «energibruk transport» | 10 kall, alle 200; noter og dimensjoner dokumentert |
| 5 | `python3 analysis/design_gate/fetch_data.py` | Dataprøver: salg (3 tabeller), 14020, 07849, 12577, 09654 + 11561-metadata | 8 kall, alle 200; 07849 bekreftet at utelatt dimensjon med elimination=True gir totalen; ett tabellsøk feilet på URL-enkoding (rettet i #6) |
| 6 | oppfølgingsskript (inline python) | 11561-uttrekk post 12.2.1 alle energiprodukter + tabellsøk «personbiler drivstofftype», «kjørelengder», «registrerte kjøretøy drivstofftype» | 200; søk avdekket 12575/12578 (alder), 11823, 12906, 13370; ett søk ga null treff |
| 7 | `python3 analysis/design_gate/analyze_design_gate.py` | Skjøtetester A/B, prikkekontroll C, nøkkelbilder D, konsistens- og magnitudekontroller | Resultater i `results/design_gate_results.json` + 8 resultat-CSV-er |
| 8 | inline python-søk «bilparken», «elbiler bestand» | Lete etter bestandstabell med ladbar-hybriddeling | Null treff; 07849 + implisitte 12577-tall står som grunnlag |
| 9 | `python3 analysis/design_gate/check_numbers.py` | Kontrollere at alle tall sitert i `01_design_gate.md` stammer fra resultatfilen; testens evne til å feile demonstrert med bevisst feilverdi før grønn kjøring | Rød ved plantet feil, deretter grønn (se skriptets logg nederst i filen) |

## Nettoppslag utført direkte (WebFetch/WebSearch)

| Kilde | URL | Formål | Utfall |
|---|---|---|---|
| SSB statistikkside, salg av petroleumsprodukter | ssb.no/energi-og-industri/olje-og-gass/statistikk/sal-av-petroleumsprodukt | Publiseringslag, 2020-brudd, bio-håndtering | Hentet; lag ca. 3 uker; brudd forklart (for lave tall 2012–2019) |
| Samme, «Om statistikken»-fane | …?fane=om | Kjøpegruppedefinisjoner, autodiesel vs anleggsdiesel, revisjonspraksis, rapportører | Hentet; autodiesel = avgiftspliktig diesel; 14 rapportører; kjøpegruppedefinisjoner ikke dokumentert der |
| SSB statistikkside, kjørelengder | ssb.no/transport-og-reiseliv/landtransport/statistikk/kjorelengder | Datagrunnlag (odometer/EU-kontroll), omfang, brudd | Hentet; bekreftet odometerbasis og kjente brudd |
| SSB energibalanse «Om statistikken» | ssb.no/energi-og-industri/statistikker/energibalanse/aar/2018-11-26?fane=om | Fordelingsmetode veitransport, henvisning omregningsfaktorer | Hentet; peker på Notater 2018/45 vedlegg A; el-fordelingsmetode ikke beskrevet |
| SSB dokumentasjonsnotat (vedleggs-URL) | ssb.no/…/_attachment/313984 | Lese brennverdier | **404** – notatet må hentes i fase 1 |
| Websøk | «SSB Notater 2018/45 energiregnskap …» | Finne notatets URL | Kandidat-URL-er funnet; PDF ikke lest |

## Oppslag utført av research-agenter (sammendrag; alle URL-er med status i kilderegisteret)

- **Agent regelverk:** Lovdata STV/LTI-dokumenter (robots-blokkert for direkte henting – i seg selv et funn for fase 1-praksis), Skatteetatens satsside (hentet: satser 2017–2026, nullsats 1.4–1.9.2026), Avgiftshistorie-landingsside (hentet: PDF-serie 2016–2026), Miljødirektoratets omsetningskravside (hentet: 19/20/21 % for 2025/2026/2027).
- **Agent eksterne kilder:** Drivkraft Norges salgsstatistikkside (hentet: SSB oppgitt som kilde; årlig xlsx 1952–; ingen månedsfil; ustabil fil-URL), NOBIL info/API/statistikk-sider (hentet: ingen historikkfunksjon; CC BY 4.0; API-nøkkel), Elhub åpne data (hentet: ingen ladesegment-gruppe), SSB copyright (hentet: NLOD), OFV (hentet: detaljdata betalt).
- **Agent intensiteter/metode:** NVE-notat om transport og kraftsystemet (hentet: 0,2/0,25/1,2 kWh/km), NVE rapport 22/2019 (hentet: ingen kWh/km-faktorer), TØI Brage-landingsside for stock-flow-artikkelen (hentet: ERTRR 2016, fagfellevurdert), RePEc for Ang 2015 (hentet: Energy Policy 86, 233–238), TØI-rapport 1689/2019-PDF (**403** – må hentes manuelt i fase 1), kandidater: ETRR 2020 om levetider, Figenbaum m.fl. 2018 (WEVJ).

## Fase 1, økt 1 (2026-08-10/11): datalag og brennverdier

| # | Kommando/oppslag | Formål | Utfall |
|---|---|---|---|
| 10 | Websøk + henting av SSB-publikasjonsside for dokumentasjonsnotatet | Finne PDF-URL for Notater 2018/45 | Funnet: `_attachment/369610` |
| 11 | WebFetch av PDF-en | Lese vedlegg A | Tidsavbrudd; byttet til nedlasting |
| 12 | `curl` av PDF (2,7 MB, 354 sider) + `pdfplumber`-søk og -lesing | Vedlegg A: tabell A1–A4 | Funnet på s. 51–53; verdier ført inn i D-0018, unit_map og energy.py |
| 13 | `pip install -e ".[dev]"` + `python -m veitransport_energi.build` | Førstegangsbygg av datalaget (16 API-kall, logget i `data/raw/request_log.csv`) | Første kjøring stoppet av kontrakt: 294 tomme celler uten statuskode i energibalanseposten (strukturell glisenhet) → egenskapen kodet eksplisitt i spesifikasjonen; deretter 8/8 OK |
| 14 | `python -m veitransport_energi.build --offline` + `pytest` + `ruff check` | Verifisere offline-bygg, testsuite og lint | 29 tester grønne uten nettverk; 4 lintfunn rettet |
| 15 | `git checkout -b feat/data-layer` + commits + bundle | Leveranse for gjennomgåbar PR | Se PR-beskrivelsen |

Merknad: ved fase 1-uttrekket inneholdt energibalanseposten (11561) også 2025-årgangen; designportens tall (til og med 2024) står uendret som daterte resultater, og ny vintage er dokumentert i `data/vintage.json`.

## Kunnskapsgrenser etter fase 0 (skal lukkes i fase 1–2)

1. Brennverdier/tettheter: Notater 2018/45 vedlegg A er ikke lest (404 på vedleggsforsøket).
2. Energibalansens fordelingsmetode for elektrisitet til veitransport er ikke dokumentert i det som er hentet.
3. Kjøpegruppedefinisjonene i salgsstatistikken er ikke dokumentert offentlig; må avklares før analytisk bruk.
4. Ikke-vei-andelen av bensinsalget er ikke tallfestet fra primærkilde (kun indikert av magnitudekontrollen).
5. Regionkodenes stabilitet gjennom fylkesreformen 2020 er ikke kontrollert (fylkesnivået er tatt ut av kjernen, så dette blokkerer ikke).
6. Forfatterlisten for ERTRR-artikkelen (Fridstrøm & Østli) skal bekreftes mot DOI-siden.
7. Drivkraft Norges xlsx er ikke faktisk lastet ned programmatisk – lenken er sett, nedlastbarhet er uprøvd.
