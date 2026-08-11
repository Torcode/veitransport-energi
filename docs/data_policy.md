# Rådatapolicy

Fastsatt i fase 1 (D-0017). Policyen avveier reproduserbarhet, sporbarhet og repostørrelse.

## Hva som versjoneres i repoet

| Innhold | Sti | Begrunnelse |
|---|---|---|
| Rå API-svar (JSON-stat2) og metadata | `data/raw/` | Bevis for hva som faktisk ble hentet; gjør bygg og tester kjørbare uten nettverk. Volumet er lite (under 10 MB) |
| Tidy-uttrekk (CSV) | `data/extracts/` | Testenes og analysenes felles faktagrunnlag |
| Vintage-manifest | `data/vintage.json` | Datavintage per tabell: kildens oppdateringstidspunkt, periodedekning, SHA-256 for råfil og uttrekk, git-commit og byggetidspunkt |
| Forespørselslogg | `data/raw/request_log.csv` | Komplett maskinell logg over alle API-kall (tidspunkt, URL, status, bytes) |

Store binærfiler, manuelt nedlastede filer og alt som ikke kan gjenskapes av `python -m veitransport_energi.build`, hører ikke hjemme i `data/`.

## Oppdatering

`python -m veitransport_energi.build --refresh` henter alt på nytt og skriver nytt vintage-manifest. Hver oppdatering committes for seg, slik at en datavintage alltid kan hentes ut som én commit. `--offline` bygger uttrekk og manifest fra eksisterende cache og brukes i CI og tester.

## Kilde og lisens

Alle data i `data/` er hentet fra Statistisk sentralbyrås åpne PxWebAPI og gjenbrukes under [NLOD](https://data.norge.no/nlod/no/2.0) med Statistisk sentralbyrå som kilde. Tabellnumre, definisjoner og kontrollstatus per kilde: [`data/metadata/source_register.csv`](../data/metadata/source_register.csv). Designportens opprinnelige uttrekk ligger urørt i `analysis/design_gate/` som fase 0-evidens; `data/` er det løpende, kanoniske laget.
