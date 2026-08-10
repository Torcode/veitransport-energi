# Prosjektcharter (fase 0)

Arbeidsnavn: `transport-energy-norway` (endelig navneanbefaling i `01_design_gate.md`)
Status: utkast fra designporten, 2026-08-10. Charteret er ikke offentlig tekst før fase 0 er godkjent av prosjekteier.

## 1. Beslutningsproblem

Den norske personbilparken skiftes ut i høyt tempo: elbiler utgjorde 94,7 prosent av førstegangsregistrerte personbiler i 2025, mot 17,9 prosent i 2015, og 32,2 prosent av personbilbestanden ved utgangen av 2025. Salget av bilbensin er halvert siden 2010 (bensinserien er ikke berørt av 2020-bruddet i dieselinnsamlingen), og autodieselsalget har falt om lag 20 prosent bare siden 2022, målt innenfor den nyeste, sammenlignbare tabellen. Samtidig er elektrisitetsbehovet fra veitransport i vekst, fra om lag 1,1 TWh i 2020 til om lag 2,8 TWh i 2024 ifølge energibalansen.

Aktører som skal planlegge i denne overgangen – energiselskaper, nettselskaper, drivstoffbransjen, offentlige etater med ansvar for avgifter, klima eller beredskap – mangler ett samlet, etterprøvbart regnestykke som kobler kjøretøyparkens sammensetning til etterspørselen etter bensin, autodiesel og elektrisitet, og som viser hvilke antakelser som driver banene framover.

Beslutningsproblemet prosjektet skal betjene er: **hvor raskt faller etterspørselen etter bensin og autodiesel, hvor mye elektrisitet vil veitransporten kreve fram mot 2035, og hvilke forutsetninger avgjør svaret.**

## 2. Foreløpig hovedestimand

Designporten anbefaler følgende presisering av hovedestimandet (endelig fastsettelse er prosjekteiers beslutning):

**Årlig energietterspørsel fra norskregistrerte personbiler, etter energibærer – bensin og autodiesel i millioner liter og GWh, elektrisitet i GWh – (a) rekonstruert historisk for perioden 2010–2025 og dekomponert i aktivitet, parksammensetning og energiintensitet, og (b) som betingede baner 2026–2035 under eksplisitte scenarioforutsetninger om nyregistrering, nettoavgang, kjørelengde og energiintensitet.**

Presiseringer som følger av designporten:

- Fysisk volum (liter) og energi (GWh) rapporteres separat, fordi overgangen mellom dem krever antakelser om biodrivstoffinnblanding og brennverdi som ennå ikke er primærkildeverifisert.
- De framtidsrettede banene er framskrivinger og scenarioer, ikke prognoser. Prosjektet tilordner dem ikke sannsynligheter.
- Varebiler behandles som sekundær modul med samme arkitektur. Tunge kjøretøy inngår bare i avstemmingslaget, ikke i estimandet.

## 3. Tiltenkte brukere

1. **Analytiker/utreder** i energiselskap, nettselskap, bransjeorganisasjon eller offentlig etat som trenger konsistente serier og et transparent scenarioverktøy.
2. **Fagdirektør/beslutningstaker** som trenger hovedbildet, driverne og usikkerheten på under fem minutter (rådgivernotat og beslutningsflate).
3. **Metodisk leser** (statistiker, forsker, revisor) som skal kunne etterprøve hvert tall fra kilde til figur.

Hver analysekomponent i prosjektet skal kunne knyttes til minst ett av disse brukerbehovene; komponenter uten slik kobling tas ut.

## 4. Offentlig hovedfortelling

Én setning: *Utskiftingen av personbilparken flytter energietterspørselen fra bensin og autodiesel til elektrisitet – dette prosjektet måler hvor langt Norge er kommet, forklarer hva som har drevet utviklingen, og viser hva som skal til for at den fortsetter, bremser eller akselererer fram mot 2035.*

Fortellingen bæres av tre spørsmål i rekkefølge: Hva har skjedd (publiserbar statistikk)? Hvorfor (dekomponering)? Hva nå (scenarioer med synlig usikkerhet)?

## 5. Forholdet mellom komponentene

| Komponent | Rolle | Klassifisering av tall |
|---|---|---|
| Historisk statistikk | Grunnmur: kvalitetssikrede serier med synlige brudd | observert / konstruert fra observerte data |
| Historisk analyse | Forklaring: dekomponering av endring i energibruk | konstruert / estimert |
| Bestand–strøm-modell | Motor: kobler nyregistrering, avgang, bestand, kjørelengde og energi | estimert / kalibrert |
| Framtidsdel | Betingede baner 2026–2035 | scenarioforutsatt |
| Usikkerhet og validering | Rammer inn alle ledd | – |

Designporten anbefaler at **prognosemodul utelates** (begrunnelse i `01_design_gate.md` og `02_method_decision.md`): månedsstatistikken publiseres med om lag tre ukers etterslep, ingen definert bruker har et operativt korttidsbehov i prosjektet, og en slik modul ville gjenta et analyseformat porteføljen allerede demonstrerer, uten å tilføre beslutningsverdi til dette produktet.

## 6. Avgrensninger

Prosjektet skal ikke:

- estimere kausale effekter av priser eller avgifter uten identifikasjonsdesign; pris- og avgiftsdata brukes deskriptivt og som scenariokontekst,
- tilordne scenarioene sannsynligheter eller utpeke en «mest sannsynlig» bane uten dokumentert grunnlag,
- skjule sammenlignbarhetsbrudd gjennom skjøting, skalering eller glatting,
- dekke luftfart, sjøfart, bane eller anleggsdiesel utenfor vei (anleggsdiesel vises kun som kontekstserie),
- modellere ladeinfrastruktur (NOBIL har verifisert ingen historikkfunksjon; utelates fra kjernen),
- publisere fylkesfordelte hovedserier (fylkesdimensjonen i salgsstatistikken opphørte i praksis i 2022 og brytes av fylkesreformene).

## 7. Offentlig informasjonsarkitektur

- **Nivå 1 – ett minutt:** README med problem, hovedfunn, én metodesetning, viktigste begrensning og lenke til beslutningsflaten.
- **Nivå 2 – beslutningsbruk:** GitHub Pages-side som viser hovedresultatet (tre energibaner, historisk og scenario), drivere, forutsetninger og usikkerhet, lest fra versjonerte resultatfiler; kort rådgivernotat.
- **Nivå 3 – etterprøvbarhet:** metodenote, kilderegister, kodebok, antakelsesregister, valideringsresultater, beslutningslogg, kode og tester.

Detaljert brukerreise og designsystem: `03_product_and_design.md`.

## 8. Roller og ansvar

Prosjekteier fastsetter problemstilling, estimand, scope og all offentlig publisering, og godkjenner merge til main, releaser og endringer i repoets synlighet. Den tekniske utførelsen, kvalitetskontrollene og dokumentasjonen bæres av prosjektets KI-assistent under eierens gjennomgang; vesentlige valg loggføres i `decision_log.md` med opphav og begrunnelse. Eierens navn brukes ikke som fortellerstemme i prosjektets faglige prosa. En presis KI-erklæring inngår i README og metodenote fra fase 1.

## 9. Status og forbehold

Alle tall i dette charteret stammer fra designportens dokumenterte uttrekk (`analysis/design_gate/`, med API-logg i `request_log.csv`) og er foreløpige arbeidsstørrelser, ikke publiserte resultater. TWh-tallene for elektrisitet er energibalansens veitransportpost; hvor uavhengig denne posten er av en modellberegning, er en navngitt kunnskapsgrense som avklares i fase 1–2.
