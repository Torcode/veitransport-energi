# Metodebeslutning (fase 0)

Dato: 2026-08-10. Prinsipp: ingen metode tas inn uten at den (1) besvarer et definert delspørsmål, (2) støttes av datagrunnlaget, (3) kan sammenlignes med en enkel baseline, (4) kan valideres uten informasjonslekkasje, (5) tilfører informasjon utover eksisterende komponenter og (6) påvirker en konklusjon, usikkerhetsvurdering eller beslutning. Matrisen under er vurdert mot dataresultatene i `01_design_gate.md`; empirien der er premiss her.

## M1 – Historisk rekonstruksjon av serier

| Felt | Innhold |
|---|---|
| Delspørsmål | Kan bestand, kjørelengde og energibruk rekonstrueres konsistent over tid? |
| Estimand | Observerte/konstruerte årsserier 2005/2008/2010–2025 og segmenterte månedsserier 1995–2026 |
| Datagrunnlag | 03687, 11174, 13585, 07849, 12576/12577, 14020, 11561 |
| Viktigste antakelser | Skjøteregler fra designporten; ingen nivåjustering over dokumenterte brudd |
| Identifikasjonsproblem | I1 (2020-bruddet), I2 (én måneds overlapp), I6 (hybrider før 2016) |
| Valideringsdesign | Datakontrakter; skjøtetestene som permanent testsuite; kontroll mot kilde-API ved hver oppdatering |
| Enkel referanse | Ubehandlede kildetabeller side om side |
| Forventet merverdi | Selve statistikkproduktet; forutsetning for alt annet |
| Beregningskostnad | Lav |
| Risiko | Å skjule brudd ved sammenstilling; motvirkes av segmentert publisering og bruddmetadata per serie |
| **Anbefaling** | **Inn.** Deterministisk, regelbasert sammenstilling med maskinlesbare bruddmarkeringer |

## M2 – Dekomponering av historisk endring

| Felt | Innhold |
|---|---|
| Delspørsmål | Hvor mye av endringen i energibruk skyldes aktivitet, parksammensetning og intensitet? |
| Estimand | Additive bidrag til endring i energi per bærer, år til år og over delperioder |
| Datagrunnlag | Kjørelengder per drivlinje (12577, 2005–2025); energi per bærer (avstemte serier fra M1/M3) |
| Viktigste antakelser | Intensitetsleddet arver kalibreringen fra M3; hybriddeling først fra 2016 |
| Identifikasjonsproblem | I5, I6; dekomponering er regnskap, ikke kausalanalyse – formidles slik |
| Valideringsdesign | LMDI-I er eksakt additiv (ingen restledd å gjemme noe i); invarianstester; delperiodesummer avstemmes mot totalendring |
| Enkel referanse | To-faktor indeksdekomponering (aktivitet × gjennomsnittsintensitet) |
| Forventet merverdi | Svar på «hvorfor»-spørsmålet; skiller struktureffekt (drivlinjemiks) fra effektivisering |
| Beregningskostnad | Lav |
| Risiko | Overfortolkning som årsaksforklaring; motvirkes med eksplisitt regnskapsspråk |
| **Anbefaling** | **Inn: LMDI-I (additiv) på identiteten energi = Σ km-andel × intensitet, 2010–2025 med hovedvekt 2016–.** Metodereferanse: Ang (2015), Energy Policy 86. SSB bruker selv LMDI i offisiell statistikk (tabell 11602), så metoden er revisjonsmessig gjenkjennelig. Reduseres til to faktorer der drivlinjedelingen ikke bærer (før 2016) |

## M3 – Bestand–strøm-modell (kjernen)

| Felt | Innhold |
|---|---|
| Delspørsmål | Hvordan omsettes nyregistrering og avgang i bestand, aktivitet og energi? |
| Estimand | bestand[f,t], km[f,t], energi[f,t] historisk; framskrivbart grunnlag for M5 |
| Datagrunnlag | 07849, 14020, 12577; intensiteter (NVE-punkt + kalibrering) |
| Viktigste antakelser | Nettoavgang som residual; tilgangsdeling bensin/diesel før 2019; utility factor for ladbare hybrider |
| Identifikasjonsproblem | I3, I4, I8; restleddene i designportens pkt. 8 |
| Valideringsdesign | Backcast 2015→2025 mot observert bestand (tester avgangsleddet gitt observert tilgang – sies eksplisitt); kryssystem-kontroll km×intensitet mot salg; konsistens 12577/07849 |
| Enkel referanse | Rene trendframskrivinger av bestand per drivlinje |
| Forventet merverdi | Mekanisk kobling politikkrelevante strømmer → energi; navet i produktet |
| Beregningskostnad | Lav |
| Risiko | Skinnpresisjon i residualleddet; motvirkes ved at nettoavgang aldri omtales som vraking og publiseres med dekomponeringsforbehold |
| **Anbefaling** | **Inn: deterministisk årlig bestand–strøm per drivlinje.** Kohort-/overlevelsesutvidelse (Weibull på alder, jf. Fridstrøm & Østli 2016, ERTRR) tas bare inn dersom fase 3 viser at aldersdataene (12575/12578) identifiserer overlevelse bedre enn residualraten – beslektet modell er fagfellevurdert for norsk bilpark, men enklere løsning foretrekkes til dokumentert behov foreligger |

## M4 – Prognosemodul

| Felt | Innhold |
|---|---|
| Delspørsmål | Finnes et selvstendig operativt behov for korttidsprognose/nåkast? |
| Prediksjonsmål (hypotetisk) | Månedlig salg av bensin/autodiesel, h=1–6 |
| Datagrunnlag | 13585 (fra 2021/2022), segmentert historikk |
| Kriterievurdering | (1) Ingen definert bruker med operativt behov i produktet. (2) Publiseringslag om lag tre uker gir minimal nåkast-gevinst. (3) Tilfører ikke informasjon utover M1+M5 for beslutningsproblemet (årlig horisont). (4) Dupliserer analyseformat porteføljen alt demonstrerer (månedsprognoser med rullerende evaluering og kalibrerte intervaller). (5) Databruddene gjør læringsvinduet kort uten at det finnes en bruker som bærer kostnaden |
| **Anbefaling** | **NEI – utelates.** Revurderes bare hvis en konkret bruker med dokumentert operativt behov identifiseres; kravlisten (horisont, informasjonssett, baseline, tidsdelt validering, punkt- og fordelingsmål, revisjonshåndtering, avgrensning mot porteføljen) står i prosjektbeskrivelsen og gjelder da uendret |

## M5 – Scenarioframskriving 2026–2035

| Felt | Innhold |
|---|---|
| Delspørsmål | Hvordan endres etterspørselen under alternative baner for nyregistrering, avgang, kjørelengde og intensitet? |
| Estimand | Betingede baner for energi[f,t] og volum, per scenario |
| Datagrunnlag | M3-tilstand per 2025 + antakelsesregister (scenario-ID, variabel, bane, enhet, gyldighet, kilde, status, ev. intervall) |
| Viktigste antakelser | Scenariobanene selv; analytisk separerbare (én dimensjon endres om gangen der det er mulig) |
| Identifikasjonsproblem | Ingen – betingede beregninger; risikoen er kommunikativ (scenario ≠ prognose) |
| Valideringsdesign | Scenarioinvarians (identiteter, ikke-negativitet, bestandskontinuitet); «backcast-scenario» der 2015-antakelser kjøres mot fasit for å illustrere metodens følsomhet |
| Enkel referanse | Teknisk videreføring (siste observerte rater holdes konstante) – publiseres som referansebane uten sannsynlighetspåstand |
| Forventet merverdi | Selve framtidsdelen av beslutningsproblemet |
| Beregningskostnad | Lav (deterministisk kjerne) |
| Risiko | At lesere tolker spennet som konfidensintervall; motvirkes av begrepsdisiplin i all formidling |
| **Anbefaling** | **Inn: deterministisk scenariomotor med separerbare dimensjoner.** Ingen sannsynlighetsrangering av scenarioer |

## M6 – Usikkerhetsanalyse

| Felt | Innhold |
|---|---|
| Delspørsmål | Hvilke parametre og antakelser forklarer mest av variasjonen i resultatene? |
| Estimand | Følsomhets- og fordelingsmål per usikkerhetstype |
| Typedeling | (a) datamåling/revisjon → dokumenterte bruddeffekter og revisjonshistorikk; (b) parameterusikkerhet → Monte Carlo innen scenario (intensiteter, utility factor, avgangsrater, km); (c) modellspesifikasjon → alternative spesifikasjoner (f.eks. residual- mot overlevelsesbasert avgang); (d) scenarioantakelser → scenariospenn |
| Valideringsdesign | MC-konvergens; sensitivitetsranger (tornado) reproduserbare fra konfig; ingen sammenslåing av usikkerhetstyper i ett bånd uten eksplisitt forklaring av hva båndet representerer |
| Enkel referanse | Én-faktor-sensitivitet (én parameter om gangen) |
| Forventet merverdi | Svar på delspørsmål 4; rangerer hva som bør overvåkes |
| Beregningskostnad | Moderat (MC), håndterbar |
| Risiko | Skinnkvantifisering av usikkerhet der grunnlaget er tynt; fordelingsantakelser dokumenteres i antakelsesregisteret |
| **Anbefaling** | **Inn: sensitivitet + Monte Carlo innen scenario, med streng typedeling.** Bootstrap bare hvis en komponent får et reelt utvalgsbasert estimeringsledd |

## Metoder vurdert og ikke tatt inn nå

- **Tilstandsrom-/dynamiske modeller:** ingen komponent har et definert filtrerings- eller signalutvinningsbehov som identiteten ikke løser enklere; gir ikke bedre svar på noe delspørsmål (kriterium 1 og 5 feiler).
- **Hierarkisk modellering på tvers av kjøretøygrupper:** aktuelt først hvis varebilmodulen aktiveres og datagrunnlaget viser delbar struktur; utsatt (kriterium 2 og 6 ennå ikke oppfylt).
- **Økonometrisk etterspørselsmodell (priselastisitet):** ingen identifikasjonsstrategi tilgjengelig i fase 0-kildene; pris/avgift forblir deskriptivt (kriterium 4 feiler; jf. charterets avgrensning). Elastisitet fra litteratur kan senere brukes som ekstern sensitivitetsantakelse, tydelig merket.
- **Maskinlæring:** det finnes ikke noe presist definert prediksjonsproblem i produktet etter at M4 er avvist (kriterium 1 feiler).
- **Probabilistisk korttidsprognose:** avvist som M4.

Litteraturreferansene med kontrollstatus (Fridstrøm & Østli 2016; Ang 2015; kandidatstatus for øvrige) står i `data/metadata/source_register.csv`.
