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

## Kodebok

`data/metadata/codebook.csv` forklarer hver kode som faktisk forekommer i uttrekkene: tabell, dimensjon, kode, etikett, enhet for statistikkvariablene, og SSBs egne noter — inkludert tabellnotene som bærer de tyngste tolkningsforbeholdene (at «annet drivstoff» i bestandstabellen hovedsakelig er hybrider, at autodieseltall fra 2020 ikke er sammenlignbare bakover, at hybrider lå i bensin/diesel til og med 2015).

Kodeboken skrives ikke for hånd. Den genereres fra de cachede metadatasvarene med `python -m veitransport_energi.codebook`, og tester krever at den dekker dataene nøyaktig: hver kode i uttrekkene skal ha en rad, ingen rad skal vise til en kode som ikke finnes, alle statistikkvariabler skal ha enhet, og den committede filen skal svare til det koden genererer nå. En kode som forsvinner eller kommer til ved neste datavintage, gir derfor rød test framfor en kodebok som stille går ut av takt.

## Innlesing av uttrekk

All lesing av `data/extracts/` skal gå gjennom `veitransport_energi.datasets.read_extract()`. Klassifikasjonskodene er strenger, og flere ser ut som tall med ledende null — kjøpegruppe `00`, produkt `01`. Med pandas' standardinnstillinger blir `00` til tallet `0`, koden matcher ikke lenger metadata eller kodebok, og feilen er stille. `read_extract` leser alle kolonner som tekst og konverterer bare `value` til tall; en egen test dokumenterer feilen funksjonen hindrer.
