# Artefakter

Maskinlesbare resultatfiler. Alt som står i README, beslutningsflate, rådgivernotat og metodenote skal leses herfra — ingen hovedtall skrives manuelt to steder. Filene bygges med `python -m veitransport_energi.artifacts` og versjoneres sammen med `release_manifest.json`, som binder dem til datavintage, kodeversjon og git-commit.

## historical_statistics.csv

Publiserbar historisk statistikk i langt format. Én rad per serie, gruppe, drivlinje og periode.

| Kolonne | Innhold |
|---|---|
| `serie_id` | `salg_bilbensin`, `salg_dieselsum`, `salg_autodiesel`, `bestand`, `kjorelengde`, `energi_bilbensin`, `energi_autodiesel` |
| `gruppe` | `personbiler`, `varebiler`, eller `veitransport_og_ovrig` for salgsserier som ikke kan fordeles på kjøretøygruppe |
| `drivlinje` | `bensin`, `diesel`, `elektrisitet`, `hybrid_ladbar`, `hybrid_ikke_ladbar`, `annet`, `uspesifisert` |
| `variabel`, `enhet` | måltall og måleenhet |
| `frekvens` | `M` eller `A` |
| `periode` | `1995M01` eller `2024` — **tekst, ikke tall**, siden serien blander frekvenser |
| `verdi` | tallverdien |
| `status` | `observert`, `konstruert` eller `estimert` (se under) |
| `kilde` | tabellnummer, og for energiserier også faktorkilden |
| `segment` | hvilken kildetabell eller hvilke kjøretøykoder raden bygger på |
| `brudd` | bruddmerking og forbehold som gjelder nettopp den raden |

**Statusverdiene** er bindende og skal aldri utelates i videre bruk: `observert` betyr at tallet står slik i kilden; `konstruert` at det er aggregert eller skjøtt av observerte tall etter de dokumenterte reglene, uten antakelser utover dem; `estimert` at det er beregnet med en parameter utenfor kilden. Framtidsrettede statuser (`scenarioforutsatt`) hører til fase 5 og forekommer ikke i denne filen.

To forbehold er verdt å lese før tallene brukes. Energiseriene er beregnet fra **salgsvolum**, ikke fra kjøretøygruppenes forbruk, og bruker fossil brennverdi på hele volumet — siden iblandet biodrivstoff har lavere brennverdi, er tallene en svak overkant. Energi per kjøretøygruppe krever kalibrerte intensiteter og kommer i fase 3. Drivlinjen `uspesifisert` er en restpost: SSB undertrykker små kategorier, så summen av de fordelte drivlinjene ligger noe under kildens totalserie — inntil 0,58 prosent for varebiler i de tidligste årene. Restposten publiseres framfor å forsvinne, slik at gruppesummen stemmer eksakt.

## Kontrolltabeller

`control_group_sums.csv` viser at drivlinjene summerer til kildens total, og hvor stor restposten er per år og gruppe. `control_stock_vs_activity.csv` er koblingskontrollen fra D-0020: implisitt antall kjøretøy i bruk mot registrert bestand per 31.12, for hver kandidatkobling. `control_energy_reconciliation.csv` avstemmer salgsenergi mot energibalansens veitransportpost (D-0019) — forholdstallet ligger mellom 0,96 og 1,01 i hele 2010–2024.

## release_manifest.json

Byggetidspunkt, git-commit, kodeversjon, Python-versjon, datavintage per kildetabell med SSBs oppdateringstidspunkt og sjekksum, og SHA-256 for hver artefaktfil.
