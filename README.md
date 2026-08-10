# veitransport-energi

Statistikk- og beslutningsgrunnlag for energiomstillingen i norsk veitransport: hvordan utskiftingen av personbilparken omsettes i etterspørsel etter bensin, autodiesel og elektrisitet – historisk og i betingede scenarioer fram mot 2035.

**Status: under utvikling, fase 1 av 7.** Designporten (fase 0) ble gjennomført og godkjent 2026-08-10. Hovedtall, figurer og beslutningsflate publiseres først når datalaget og kontrollene i fase 1–2 er på plass; det som ligger her nå, er designdokumentene, kilderegisteret og designportens etterprøvbare analysegrunnlag.

## Hva designporten fant

Fire funn bærer designet, alle med belegg i [docs/01_design_gate.md](docs/01_design_gate.md) og beregningsgrunnlag i [analysis/design_gate/](analysis/design_gate/): (1) salgsstatistikkens tre SSB-tabeller kan kobles til én konsistent månedsserie for bensin og dieselsum via petroleumsmåltallet – skjøtene er empirisk testet i alle overlappsmåneder – men autodieselserien må segmenteres ved et dokumentert innsamlingsbrudd i 2020 og skjøtes ikke; (2) kjørelengdestatistikken er odometerbasert og gir et målesystem uavhengig av salgsstatistikken, som muliggjør reell kryssvalidering; (3) elektrisitetsbehovet må modelleres – det finnes ingen salgsstatistikk for strøm til veitransport – og avstemmes mot energibalansens veitransportpost med en navngitt metodegrense; (4) elandelen i nyregistrerte personbiler var 94,7 prosent i 2025, mot 17,9 prosent i 2015, og det er denne utskiftingsdynamikken scenarioene skal betinge på.

## Innhold

| Sti | Innhold |
|---|---|
| [docs/00_project_charter.md](docs/00_project_charter.md) | Beslutningsproblem, hovedestimand, brukere, avgrensninger |
| [docs/01_design_gate.md](docs/01_design_gate.md) | Datamatrise, sammenlignbarhetsanalyse, identifikasjonsproblemer, GO-vurdering |
| [docs/02_method_decision.md](docs/02_method_decision.md) | Metodebeslutningsmatrise, inkludert begrunnet nei til prognosemodul |
| [docs/03_product_and_design.md](docs/03_product_and_design.md) | Brukerreise, informasjonsarkitektur, designsystem |
| [docs/decision_log.md](docs/decision_log.md) | Daterte beslutninger med alternativer, begrunnelse og opphav |
| [docs/command_log.md](docs/command_log.md) | Alle kommandoer og kildeoppslag i fase 0 |
| [data/metadata/source_register.csv](data/metadata/source_register.csv) | 27 kilder med definisjoner, lisens og kontrollstatus |
| [data/metadata/unit_map.csv](data/metadata/unit_map.csv) | Enheter og konverteringer med kilde og kontrollstatus |
| [analysis/design_gate/](analysis/design_gate/) | Uttrekksskript, API-logg, cachede svar, testresultater |

## Reproduserbarhet

Alle fase 0-uttrekk går mot SSBs PxWebAPI v2-beta med skriptene i `analysis/design_gate/`; hvert API-kall er logget i `request_log.csv`, og alle tall som siteres i designdokumentene kontrolleres maskinelt mot beregningsresultatene (`check_numbers.py`, 48 kontroller som er demonstrert å kunne feile). Full miljøoppskrift og én dokumentert byggkommando kommer i fase 1; fram til da er skriptene kjørbare enkeltvis med Python 3.11+ og pandas.

## Databruk og lisens

Kode og originalt innhold i dette repoet er MIT-lisensiert ([LICENSE](LICENSE)). Data avledet fra Statistisk sentralbyrå gjenbrukes under [NLOD](https://data.norge.no/nlod/no/2.0) med SSB som kilde; tabellnumre og uttrekksdatoer står i kilderegisteret. Øvrige kilder (Lovdata, Skatteetaten, Miljødirektoratet, NVE, Drivkraft Norge, NOBIL) har vilkår som dokumentert per kilde i [source_register.csv](data/metadata/source_register.csv); innhold derfra siteres, men redistribueres ikke her uten avklaring.

## KI-erklæring

En KI-assistent (Claude) har, under prosjekteiers styring og gjennomgang, utført datainnhenting, kontrollberegninger, kode og dokumentutkast. Maskinelt kontrollert: API-uttrekkene (logget), skjøtetestene og samsvaret mellom siterte tall og beregningsresultater. Verifisert mot primærkilder: kildene med kontrollstatus «verifisert» i kilderegisteret; uverifiserte punkter er eksplisitt merket der, og energitall for flytende drivstoff holdes utenfor offentlige hovedtall til brennverdikilden er lest (beslutning D-0011). Framtidsrettede resultater vil være framskrivinger og scenarioer, ikke prognoser, og merkes slik. Under arbeid: datalag, historisk statistikk, modell, scenarioer og beslutningsflate (fase 1–6). Faglige beslutninger, godkjenninger og all publisering er prosjekteiers ansvar; beslutningenes opphav er loggført i [decision_log.md](docs/decision_log.md).

## Veikart

Fase 0 designport (fullført og godkjent) → fase 1 datalag og kilderegister → fase 2 publiserbar historisk statistikk → fase 3 strukturell modell og validering → fase 4 utgår (prognosemodul avvist i designporten) → fase 5 scenarioer og usikkerhet → fase 6 beslutningsflate, rådgivernotat og metodenote → fase 7 release-revisjon. Arbeidet skjer i fasebrancher med gjennomgåbare pull requests; `main` er releasegren.
