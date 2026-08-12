# veitransport-energi

[![pr-kontroller](https://github.com/Torcode/veitransport-energi/actions/workflows/pr-checks.yml/badge.svg)](https://github.com/Torcode/veitransport-energi/actions/workflows/pr-checks.yml) — lint og 131 tester uten nettverk, mot committede uttrekk, samt en kontroll av at R-laget leser de samme tallene som Python. Nettverkskrevende kildekontroller inngår ikke og kjøres manuelt.

Statistikk- og beslutningsgrunnlag for energiomstillingen i norsk veitransport: hvordan utskiftingen av person- og varebilparken omsettes i etterspørsel etter bensin, autodiesel og elektrisitet — historisk, og i betingede scenarioer fram mot 2035.

**Status: fase 3 av 7 gjennomført** (fase 4 utgår; prognosemodul er avvist med begrunnelse). Datalaget, den historiske statistikken og modellkjernen med validering ligger her. Scenarioer, beslutningsflate og rådgivernotat gjenstår. Sist oppdatert etter beslutning D-0032.

## Hva vi vet

**Salget faller, men kildene tåler ikke én linje.**

![Salget av bensin og autodiesel](figurer/salg_segmentert.png)

Bensinserien er skjøtt over tre SSB-tabeller fordi skjøtene er empirisk testet i alle overlappsmåneder. Autodieselserien er det ikke: innsamlingen ble lagt om i 2020, og segmentene står derfor atskilt. Nivåforskjellen over bruddet kan ikke leses som utvikling. Innenfor det siste segmentet er fallet reelt — fra 2 872 millioner liter i 2020 til 2 301 i 2025, mens bensin gikk fra 968 til 824.

**Elbilene kjører mer enn resten av parken.**

![Elbilenes andel av bestand og kjørelengde](figurer/elandel_bestand_mot_kjorelengde.png)

I 2025 er 32,2 prosent av personbilbestanden elektrisk, men elbilene står for 36,5 prosent av de kjørte kilometerne. Det er trafikkarbeidet som fortrenger drivstoff, så en framskriving som går rett fra bestandsandel til energibruk, undervurderer fortrengningen. Forholdet var motsatt før 2015, da elbiler ble kjørt omkring halvparten så langt som resten av parken.

**To uavhengige målesystemer stemmer på totalen.** Salgsstatistikkens energiinnhold og energibalansens veitransportpost ligger innenfor 0,96–1,01 av hverandre for 2010–2024, med 0,98 som typisk forhold. Avstemmingen holder på summen, men ikke per produkt — og den grensen står navngitt framfor å bli skjult.

**Modellen treffer på ti års horisont, men bare der data rekker.** En kohortmodell som bygger aldersfordelingen fra tilgangshistorikken og estimerer overlevelse mot observert bestand, bommer med høyst 2,03 prosent over ti år som ikke inngikk i estimeringen. Den enklere modellen med konstant avgangsrate bommet med 6,8 og 7,3 prosent. Reestimering på rullerende vinduer viser hva bestandsdata faktisk identifiserer: levetidsnivået er godt bestemt (4–10 prosents spredning), mens formen på avgangskurven ikke er det (40–45 prosent). Bare sju prosent av elbilbestanden i 2025 er over åtte år, så kurvens hale er ekstrapolasjon.

**Én sentral parameter lar seg ikke identifisere fra prosjektets data.** Utility factor for ladbare hybrider — andelen kjørelengde på forbrenningsmotor — gir implisert elandel fra under 0 til over 1 når elbilintensiteten varieres innenfor sitt eget usikkerhetsspenn. Den må komme utenfra og behandles som sensitivitetsparameter, aldri som kalibrert størrelse.

Notatet [notat/hva_vi_vet.qmd](notat/hva_vi_vet.qmd) utdyper hvert punkt med hva figurene viser, hvorfor de er relevante, hvordan dataene produserer mønsteret og hvilke begrensninger som gjelder.

## Hvor vi er

| Fase | Innhold | Status |
|---|---|---|
| 0 | Designport: datamatrise, sammenlignbarhet, metodebeslutning | gjennomført |
| 1 | Datalag: uttrekk, kontrakter, kodebok, kilderegister | gjennomført |
| 2 | Publiserbar historisk statistikk med kontrolltabeller | gjennomført |
| 3 | Strukturell modell og historisk validering | gjennomført |
| 4 | Prognosemodul | utgår — avvist i metodebeslutningen |
| 5 | Scenarioer og usikkerhet | gjenstår |
| 6 | Beslutningsflate, rådgivernotat, metodenote | gjenstår |
| 7 | Releaserevisjon | gjenstår |

Arbeidet skjer i fasebrancher med gjennomgåbare pull requests; `main` er releasegren. Hver material beslutning er datert og begrunnet i [decision_log.md](docs/decision_log.md), med alternativer og opphav.

## Hva som skjer videre

Fase 5 skal bære to dokumenterte usikkerheter eksplisitt framfor å skjule dem i punktanslag: formen på overlevelseskurven, som framskrivingen er langt mer følsom for enn modellens historiske tilpasningsfeil skulle tilsi, og utility factor, som ikke lar seg identifisere fra egne data. Scenarioene skal betinge på utskiftingsdynamikken i nyregistreringene, og hvert framtidsrettet resultat merkes som framskriving, scenario, kontrafaktisk beregning eller sensitivitetsanalyse — aldri som prognose.

To åpne kildepunkter følger med: aldersfordelt bruktimport fra Statens vegvesen ville gjort kohortmodellens importalder observert framfor antatt, og ICCTs tall for utility factor er identifisert, men theicct.org blokkerer maskinell henting.

## Innhold

| Sti | Innhold |
|---|---|
| [artifacts/](artifacts/) | Alle resultatfiler, med `release_manifest.json` som binder dem til datavintage, kodeversjon og commit |
| [src/veitransport_energi/](src/veitransport_energi/) | Uttrekk, datakontrakter, serier, modeller og artefaktbygging |
| [R/](R/) | Uavhengig lesing av artefaktene, designsystem og figurer |
| [notat/](notat/) | Quarto-notater bygget utelukkende fra publiserte artefakter |
| [tests/](tests/) | 131 tester, alle demonstrert å kunne feile før de ble beholdt |
| [docs/00_project_charter.md](docs/00_project_charter.md) | Beslutningsproblem, hovedestimand, brukere, avgrensninger |
| [docs/01_design_gate.md](docs/01_design_gate.md) | Datamatrise, sammenlignbarhetsanalyse, identifikasjonsproblemer |
| [docs/02_method_decision.md](docs/02_method_decision.md) | Metodebeslutningsmatrise, inkludert begrunnet nei til prognosemodul |
| [docs/03_product_and_design.md](docs/03_product_and_design.md) | Brukerreise, informasjonsarkitektur, designsystem |
| [docs/04_scenario_design.md](docs/04_scenario_design.md) | Hva scenarioene betinger på, og hva estimandet dekker |
| [docs/decision_log.md](docs/decision_log.md) | Daterte beslutninger med alternativer, begrunnelse og opphav |
| [docs/data_policy.md](docs/data_policy.md) | Rådatapolitikk, kodebok, kanonisk innlesing |
| [data/metadata/source_register.csv](data/metadata/source_register.csv) | 29 kilder med definisjoner, lisens og kontrollstatus |

## Arbeidsdeling mellom Python og R

Python eier alt som er beregning: uttrekk fra API, datakontrakter, skjøting, enhetsomregning, modeller, validering og bygging av artefakter. R eier framstillingen: figurer, notater og en uavhengig lesing av leveransen.

Skillet er ikke smakssak. Ingen størrelse som ender i en figur eller en tekst, regnes ut i R — filtrering og sammenstilling for framstilling er tillatt, estimering og avledning er det ikke. Ellers ville prosjektet hatt to sannheter, og verifikasjonskontrakten forbyr det. Til gjengjeld kjøper R-laget noe konkret: at et annet verktøysett kan reprodusere manifestets sjekksummer og lese hver tabell uten prosjektets egen kode. Klarer det ikke det, er artefaktene mellomregninger og ikke et produkt. Kontrollen kjører i CI, og et hopp over den regnes som feil.

## Reproduserbarhet

```
pip install -e ".[dev]"                      # Python-laget
python -m veitransport_energi.artifacts      # bygger alle artefakter og manifestet
pytest                                       # 131 tester, uten nettverk
Rscript R/kontroll_artefakter.R              # uavhengig kontroll av leveransen
Rscript R/bygg_figurer.R                     # figurene i figurer/
```

R-laget krever `r-base` med `ggplot2`, `readr`, `dplyr`, `tidyr`, `scales`, `jsonlite`, `digest` og `ragg`, og en UTF-8-locale — uten den ødelegges norske tegn stille under parsing av kildefilene, og oppstartsfilen stanser derfor framfor å produsere figurer med feil tekst.

Uttrekkene i `data/extracts/` er committet, så testene kjører uten nett. Hvert API-kall er logget i `docs/command_log.md` og `analysis/design_gate/request_log.csv`.

## Databruk og lisens

Kode og originalt innhold er MIT-lisensiert ([LICENSE](LICENSE)). Data avledet fra Statistisk sentralbyrå gjenbrukes under [NLOD](https://data.norge.no/nlod/no/2.0) med SSB som kilde; tabellnumre og uttrekksdatoer står i kilderegisteret. Øvrige kilder (Lovdata, Skatteetaten, Miljødirektoratet, NVE, Drivkraft Norge, NOBIL) har vilkår dokumentert per kilde i [source_register.csv](data/metadata/source_register.csv); innhold derfra siteres, men redistribueres ikke her uten avklaring.

## KI-erklæring

En KI-assistent (Claude) har, under prosjekteiers styring og gjennomgang, utført datainnhenting, kontrollberegninger, kode og dokumentutkast. Maskinelt kontrollert: API-uttrekkene (logget), datakontraktene, skjøtetestene, samsvaret mellom siterte tall og beregningsresultater, modellenes tidsdelte validering, og at R-laget leser de samme tallene som Python. Verifisert mot primærkilder: kildene med kontrollstatus «verifisert» i kilderegisteret; uverifiserte punkter er eksplisitt merket der.

Framtidsrettede resultater vil være framskrivinger og scenarioer, ikke prognoser, og merkes slik. Faglige beslutninger, godkjenninger og all publisering er prosjekteiers ansvar; beslutningenes opphav er loggført i [decision_log.md](docs/decision_log.md), der også tilfeller der assistenten korrigerer sitt eget tidligere arbeid, står med dato og begrunnelse.
