# Designport (fase 0): datagjennomførbarhet og anbefalt design

Dato: 2026-08-10. Grunnlag: metadata og dataprøver hentet fra SSBs PxWebAPI v2-beta samme dag (skript og komplett API-logg i `analysis/design_gate/`), verifiserte nettkilder (kontrollstatus i `data/metadata/source_register.csv`) og SSBs egne noter. Alle tall i dette dokumentet er beregnet i `analysis/design_gate/analyze_design_gate.py` og lagret i `analysis/design_gate/results/design_gate_results.json`; ingen tall er gjengitt fra hukommelse eller sekundærkilder.

## 1. Hva porten har prøvd

Porten skulle avgjøre om hovedproblemstillingen – hvordan utskiftingen av kjøretøyparken omsettes i etterspørsel etter bensin, autodiesel og elektrisitet fram mot 2035 – kan besvares med tilgjengelige data, og med hvilket scope, hvilken frekvens og hvilke restledd. Testene omfattet: (i) empirisk skjøtetest av de tre salgstabellene i alle overlappsmåneder, (ii) kontroll av prikking og måltall i 13585, (iii) kartlegging av bestands-, kjørelengde- og registreringsdata med drivlinjedeling, (iv) konsistenskontroll mellom uavhengige målesystemer (kjøretøyregister/odometer mot salg og energibalanse), og (v) verifisering av regelverks- og faktakilder.

## 2. Datamatrise

Kolonnen «status» oppsummerer kontrollstatus per 2026-08-10; detaljert kontrollstatus, lisens og URL per kilde står i `data/metadata/source_register.csv`.

| Kilde | Innhold | Frekvens | Dekning | Drivlinje-/produktdeling | Status og viktigste begrensning |
|---|---|---|---|---|---|
| SSB 03687 | Salg petroleumsprodukter (mill. liter) | Måned | 1995M01–2016M07 | Bilbensin; udelt «Diesel»; fylke | Verifisert via API. Avsluttet. «Diesel» er sum av auto- og anleggsdiesel (empirisk bekreftet, pkt. 3.1) |
| SSB 11174 | Salg petroleumsprodukter (mill. liter) | Måned | 2010M01–2022M01 | Bilbensin, autodiesel, anleggsdiesel; fylke | Verifisert via API. Avsluttet. Dokumentert brudd 2020 for autodiesel/marine gassoljer/total |
| SSB 13585 | Salg petroleum og flytende biodrivstoff (mill. liter) | Måned | 2021M01–2026M06, levende | Tre måltall: totalt, petroleum inkl. iblandet bio, rent bio | Verifisert via API. 2021 prikket for totalt/rent bio; petroleumsmåltallet komplett fra 2021M01. Ingen fylkesdimensjon |
| SSB 14020 | Førstegangsregistrerte kjøretøy | Måned | 1995M01–2026M07 | El/nullutslipp, fossil (udelt), hybrid, annet × ny/bruktimport | Verifisert via API. Fossil ikke delt i bensin/diesel |
| SSB 07849 | Kjøretøybestand per 31.12 | År | 2008–2025 | Bensin, diesel, parafin, gass, el, annet («annet» hovedsakelig hybrid, iflg. SSB-note) | Verifisert via API. Hybrider kan ikke skilles ut; kommunenivå finnes |
| SSB 12576/12577 | Kjørelengder (mill. km og km per kjøretøy) | År | 2005–2025 | Full deling: bensin, diesel, el, ladbar/ikke-ladbar hybrid (bensin/diesel), gass, hydrogen | Verifisert via API. Hybrider lå i bensin/diesel til og med 2015; modellendring 2018; registerbytte 2020 |
| SSB 12575/12578 | Kjørelengder etter alder | År | 2005–2024 | Som over, pluss alder | Identifisert via API-søk; ikke uttrukket i fase 0 |
| SSB 09654 | Drivstoffpriser (kr/liter) | Måned | 1986M08–2026M06 | Bensin 95, avgiftspliktig diesel | Verifisert via API |
| SSB 11561 | Energibalansen, post 12.2.1 Veitransport | År | 1990–2024 | Bensin (ekskl. bio), autodiesel (ekskl. bio), flytende biobrensler, elektrisitet m.fl.; PJ og GWh | Verifisert via API. Fordelingsmetoden for elektrisitet til veitransport er ikke avklart (kunnskapsgrense) |
| Skatteetaten | Satser veibruksavgift 2017–2026 (HTML) og «Avgiftshistorie» (PDF 2016–2026) | År | Se kilde | Per drivstofftype, kr/liter | Satsside verifisert (hentet); PDF-ene identifisert, ikke lest |
| Lovdata | Avgiftsvedtak (STV) og produktforskriften kap. 3 | År | Vedtak minst 2012–, endringer minst 2010– | – | URL-er identifisert; direkte henting robots-blokkert; innhold verifisert via Skatteetaten/Miljødirektoratet |
| Miljødirektoratet | Omsetningskrav biodrivstoff veitrafikk | År | 2025: 19 %, 2026: 20 %, 2027: 21 % (volumprosent) | – | Verifisert (hentet). Historiske nivåer rekonstruerbare fra endringsforskrifter |
| Drivkraft Norge | Årlig salg 1952– (xlsx) | År | 1952– | Hovedprodukter | Verifisert: siden oppgir selv SSB som kilde. Fil-URL finnes, men er ikke stabil; månedstall publiseres ikke som fil |
| NOBIL | Ladestasjoner | Nå-situasjon | – | – | Verifisert negativt: ingen historikkfunksjon. Utelates fra kjernen |
| NVE-notat (Spilde/Skotland) | Energiintensitet elbil | Punktverdier | ca. 2016–17 | Personbil 0,2 kWh/km; varebil 0,25; buss/lastebil 1,2 | Verifisert (hentet). Ladetap ikke omtalt; alder er en svakhet; behandles som scenarioparameter |
| SSB Notater 2018/45, vedlegg A | Brennverdier og tettheter | – | – | – | Identifisert som kilden for omregningsfaktorer; ikke lest ennå (404 på ett vedleggsforsøk). Skal leses i fase 1 |

## 3. Sammenlignbarhetsanalyse for salgsstatistikken

### 3.1 Skjøten 03687 → 11174 (79 overlappsmåneder, 2010M01–2016M07)

Månedsvise avvik i «hele landet, alle kjøpegrupper» (beregnet på identiske måneder; fullstendige rater i `results/splice_monthly_03687_11174.csv`):

| Produktkobling | Snittforhold 11174/03687 | Median abs. avvik | Maks abs. avvik | Andel måneder over 1 % | Korrelasjon månedsvekst |
|---|---|---|---|---|---|
| Bilbensin (03 mot 03) | 0,9993 | 0,0 % | 5,3 % | 2,5 % | 0,993 |
| Diesel 03687 mot autodiesel+anleggsdiesel | 0,9996 | 0,0 % | 2,5 % | 1,3 % | 0,998 |
| Diesel 03687 mot autodiesel alene | 0,7630 | 23,5 % | 29,9 % | 100 % | 0,928 |
| Total (00 mot 00) | 0,9776 | 1,1 % | 10,8 % | 50,6 % | 0,943 |

Tolkning. For bilbensin er tabellene i praksis samme serie; de få avvikene er enkeltmåneder og ser ut som revisjoner (medianavviket er null). Det gamle produktet «Diesel» i 03687 svarer til summen av autodiesel og anleggsdiesel i 11174 – autodiesel alene ligger i snitt 24 prosent under og kan derfor ikke forlenges bakover før 2010 uten en fordelingsantakelse. Totalene har ulikt produktomfang (03687 omfatter blant annet bunkers) og skal ikke skjøtes. Sesongprofilene er like på tvers av tabellene (korrelasjon 0,9998 for bensin og 0,9997 for dieselsummen), så skjøten forstyrrer ikke sesongmønsteret.

### 3.2 Skjøten 11174 → 13585 (én overlappsmåned, 2022M01)

I den ene fellesmåneden er 13585-måltallet «sal av petroleumsprodukt (inkl. iblanda bio)» **identisk** med 11174 for alle tre veirelevante produkter (avvik 0,0 prosent for bilbensin, autodiesel og anleggsdiesel). 13585-måltallet «totalt sal» ligger 2,2 prosent over for autodiesel og 1,4 prosent over for anleggsdiesel; differansen er rent (uinnblandet) biodrivstoff, som er nytt eget måltall i 13585.

Hva én måned ikke kan teste: om avvikene varierer over sesongen, hvordan revisjonspraksis slår ut over tid, og om nivålikheten holder i andre måneder. Det som likevel er etablert, er at måltallet «petroleum inkl. iblandet bio» er definisjonsmessig kontinuerlig fra 11174 til 13585 (samme produsent, samme produktkoder i ny drakt, eksakt likhet i fellesmåneden). Skjøtens gjenstående risiko er dermed revisjonsrisiko, ikke definisjonsrisiko. Dette formuleres eksplisitt i metodenoten.

### 3.3 Bruddet i 2020 (gjelder begge nyere tabeller)

SSBs noter til 11174 og statistikksiden dokumenterer at innsamlede tall for autodiesel og marine gassoljer var for lave i 2012–2019, at dette ble korrigert fra og med 2020, og at tall fra og med 2020 for disse produktene og totalen ikke er sammenlignbare med tidligere perioder. Konsekvens for designet: autodieselserien publiseres som to segmenter (2010–2019 og 2020–) med synlig bruddmarkering; det lages ingen nivåjustert lang serie. Bilbensin er ikke omfattet av bruddet.

### 3.4 Prikking og måltall i 13585

2021-årgangen er prikket («..») for måltallene «totalt sal» og «rent biodrivstoff» (96 celler i uttrekket), mens **petroleumsmåltallet er komplett fra 2021M01**. Fra 2022 er totalen komplett, og rent bio har 75–90 prosent dekning avhengig av år og produkt. Rent biodrivstoff utgjorde 2,2 prosent av totalvolumet for autodiesel i 2025; for bilbensin er rent bio null i uttrekket. Konsekvens: den gjennomgående månedsserien 2010M01–2026M06 bygges på petroleumsmåltallet (inkl. iblandet bio); totalvolum inkl. rent bio vises som tilleggsserie fra 2022.

### 3.5 Fylkesdimensjonen og kjøpegrupper

13585 mangler fylke; regional serie opphører i praksis 2022M01, og fylkesreformene 2020/2024 endrer regionkodene underveis. Regionalt nivå tas derfor ut av kjerneproduktet (kontekstbruk kan vurderes i fase 2, men stabiliteten i regionkodene gjennom 2020-reformen er fortsatt uverifisert). Kjøpegruppene er en bransjespesifikk inndeling (SSB: utarbeidet med oljeselskapene, brukes ikke i annen statistikk); «bensin-, automat- og containerstasjoner» m.fl. er kandidat til en deskriptiv veitrafikk-avgrensning av dieselsalget, men definisjonene er ikke dokumentert i «Om statistikken» og må avklares i fase 1 før de brukes analytisk.

## 4. Anbefalt kjøretøy- og produktavgrensning

**Kjerne: personbiler.** Begrunnelse: alle nødvendige ledd finnes med drivlinjedeling og lang dekning – bestand (07849, 2008–2025), kjørelengder i sum og per kjøretøy (12577, 2005–2025), førstegangsregistreringer (14020, 1995–), og energiintensiteter har i det minste én verifisert kilde for el (NVE) og en identifisert kilde for forbrenningsmotorer (HBEFA-faktorene i SSBs veitrafikkmodell; TØI). Personbiler bærer også hovedfortellingen: 94,7 prosent el-andel i nyregistreringene i 2025.

**Sekundær modul: varebiler** (samme arkitektur; 07849 «Varebiler», 12577 små/store varebiler, 14020 «Vare- og campingbiler»). Kategoriene er ikke identisk avgrenset på tvers av tabellene; koblingskontroll gjøres i fase 1 før modulen aktiveres.

**Avstemmingslag: hele veitransporten.** Salg av autodiesel kan ikke avgrenses til personbiler; tunge kjøretøy og busser bruker samme produkt. Avstemming av modellert energibruk mot salg og energibalanse skjer derfor på veitransportnivå, der de tunge gruppenes kjørelengder (12576/12577) og intensitetsantakelser inngår som eksplisitte, synlige restposter – ikke i estimandet.

**Produkter: bilbensin og autodiesel (petroleumsmåltallet), elektrisitet.** Anleggsdiesel vises kun som kontekstserie. Rent bio som tilleggsserie fra 2022. En vesentlig, tallfestet lekkasje må navngis: energibalansens veitransportpost for bensin svarer til en implisitt brennverdi på bare 22,6–24,6 MJ per liter mot solgt volum (2023–2024), mens autodiesel gir 32,2–32,6. Avviket for bensin er for stort til å skyldes bio-innblanding alene og indikerer at en betydelig del av bensinvolumet allokeres utenfor veitransportposten (fritidsbåter, motorredskaper mv.) eller håndteres annerledes i balansen. Hvor stor ikke-vei-andelen faktisk er, er en navngitt kunnskapsgrense som skal avklares mot energibalansens dokumentasjon i fase 1–2; inntil da avstemmes bensin mot salgsstatistikken, ikke mot energibalanseposten alene.

## 5. Anbefalt frekvens per delproblem

| Delproblem | Frekvens | Begrunnelse |
|---|---|---|
| Publiserbar salgsstatistikk | Måned (segmentert) | Kildenes egen frekvens; brudd vises, ikke skjules |
| Bestand–strøm-modell | År | Bestand, kjørelengder og energibalanse er årlige; månedsdynamikk tilfører ikke identifikasjon |
| Dekomponering | År | Kjørelengdedata 2005–2025 er årlige |
| Scenarioer 2026–2035 | År | Beslutningshorisonten er årlig; månedsscenarioer gir falsk presisjon |
| Priser/avgifter (kontekst) | Måned/år | 09654 er månedlig; satser er årlige |

## 6. Enhetskart

Fullt enhetskart med konverteringer, kilder og kontrollstatus: `data/metadata/unit_map.csv`. Bærende prinsipper: volum (mill. liter) og energi (GWh) publiseres som separate størrelser; omregning liter→energi krever brennverdi × tetthet der kilden (SSB Notater 2018/45, vedlegg A) er identifisert, men ennå ikke lest – fram til den er verifisert, merkes alle energitall for flytende drivstoff som «konstruert med uverifisert faktor» og holdes ute av offentlige hovedtall. Elbilens kWh/km (NVE: 0,2 for personbil) behandles som scenarioparameter med dokumentert svakhet (alder, uavklart ladetap), ikke som fakta. Rene enhetsomregninger (mill. liter→liter, PJ→GWh, MJ→kWh) er matematiske identiteter.

## 7. Modellidentiteter og klassifisering av ledd

Bestandsdynamikk per drivlinje f (år t):

    bestand[f, t+1] = bestand[f, t] + tilgang[f, t] − nettoavgang[f, t]

- bestand: observert (07849, per 31.12)
- tilgang: observert (14020, førstegangsregistrert = nye + bruktimport)
- **nettoavgang: konstruert residual.** Den omfatter vraking, eksport, avregistrering og omklassifisering og skal aldri omtales som «vraking».

Energietterspørsel per drivlinje:

    energi[f, t] = kjørelengde_total[f, t] × energiintensitet[f, t]

der kjørelengde_total (mill. km) er **direkte observert** i 12577 for 2005–2025 – identiteten trenger altså ikke gå veien om bestand × gjennomsnittskjørelengde historisk. Bestand–strøm-modellen trengs for å *framskrive* kjørelengdegrunnlaget (bestand → km via kjørelengde per kjøretøy), mens historisk energi kan bygges på observert aktivitet. For framskriving:

    energi[f, t] = bestand[f, t] × kjørelengde_per_kjøretøy[f, t] × energiintensitet[f, t]

Klassifisering: kjørelengder er observerte (odometerbaserte, fra EU-kontroll – et målesystem uavhengig av salgsstatistikken); intensiteter er kalibrerte (mot kompatibelt salg på riktig aggregeringsnivå) eller eksternt antatte (el); framtidige ledd er scenarioforutsatte.

Vilkårene fra prosjektbeskrivelsen er kontrollert: kategoriene kan kobles på drivlinjenivå med de restleddene som er navngitt i pkt. 8; tidsreferansene er forenlige når bestand per 31.12 kombineres med kjørelengder per kalenderår via gjennomsnittsbetraktning (dokumenteres i fase 3); kjørelengdebegrepet er konsistent 2005–2025 med to dokumenterte brudd (modell 2018, register 2020); energiintensiteten har kilde for el og identifisert kilde for forbrenning; enhetskonverteringene er kartlagt med status; og drivstoffsalgets avgrensning mot kjøretøygruppene håndteres i avstemmingslaget, ikke ved antakelse.

## 8. Nødvendige restledd og konstruerte størrelser

1. **Nettoavgang** (residual per drivlinje og år). Kontroll: backcast-avstemming mot observert bestand.
2. **Bensin/diesel-deling av fossil tilgang.** 14020 deler ikke fossil i bensin og diesel. Etter 2020 er fossilstrømmen liten (4 218 nye fossile personbiler i 2025); historisk (2010–2019) må delingen rekonstrueres (kandidat: SSB 12906 for 2019–, bestandsdifferanser, eller dokumentert bransjekilde). Fram til det: nettoavgang identifiseres presist for el og for fossil samlet, og bare med antatt tilgangsdeling for bensin mot diesel.
3. **Hybridbestand.** 07849 legger hybrider i «annet drivstoff»; ladbar/ikke-ladbar deling finnes bare i kjørelengdetabellene fra 2016. Implisitt bestand-i-bruk (total km / km per kjøretøy) brukes som konstruert hybridserie, tydelig merket. Kontroll mot 07849: implisitt antall ligger 4,0 prosent (el), 5,8 prosent (bensin) og 15,7 prosent (diesel) over 31.12-bestanden i 2025 – som ventet, siden 12577 omfatter kjøretøy som var registrert i løpet av året; avviksmønsteret dokumenteres og overvåkes.
4. **El-andel for ladbare hybrider** (utility factor): ren antakelse med kilde (kandidat: Figenbaum m.fl. 2018); scenarioparameter.
5. **Ikke-vei-andel av bensinsalget** (jf. pkt. 4): navngitt restpost i avstemmingen.

## 9. Viktigste identifikasjonsproblemer

- **I1 – Autodieselbruddet 2020:** dokumentert for lav innsamling 2012–2019; ingen bakoverkorrigering finnes. Håndteres med segmentering; nivåendringer over bruddet tolkes ikke.
- **I2 – Én måneds overlapp 11174/13585:** revisjonsrisiko i skjøten kan ikke testes empirisk utover definisjonskontinuiteten (pkt. 3.2); navngis i metodenoten.
- **I3 – Aggregeringsproblemet for diesel:** salg kan ikke observeres per kjøretøygruppe; personbilenes dieselbruk er modellert, bare veitransportnivået kan avstemmes.
- **I4 – Elektrisitet mangler salgsstatistikk:** el-etterspørselen er gjennomgående modellert; energibalansens el-post kan bygge på beslektet metodikk (uavklart) og er dermed bare delvis uavhengig.
- **I5 – Intensiteter:** ingen løpende offisiell norsk serie for flåtens l/mil; kalibrerte intensiteter arver alle feil i salgsallokering og km-måling (feilene «pakkes» i intensitetsleddet og må presenteres slik).
- **I6 – Hybrider før 2016** ligger i bensin/diesel i kjørelengdestatistikken og i «annet» i bestanden; dekomponeringen får svakere strukturledd før 2016.
- **I7 – Pris/avgift:** ingen kausal identifikasjon uten design; holdes deskriptivt (jf. charterets avgrensning).
- **I8 – Bruktimport/eksport** inngår i tilgang/nettoavgang uten egen eksportstatistikk i de identifiserte kildene; nettoavgang må derfor ikke tolkes som levetid alene.

## 10. Valideringsmuligheter

| Kontroll | Innhold | Status/merknad |
|---|---|---|
| Datakontrakter | Skjema, enheter, dubletter, hull, prikkede celler | Fase 1; PR-tester uten nettverk |
| Skjøtetester | Pkt. 3.1–3.2 som permanente, kjørbare tester | Implementert i fase 0-skript; flyttes inn i testsuiten |
| Regnskapsidentitet bestand | bestand+tilgang−avgang avstemmes mot 07849 (backcast fra 2015) | Tester avgangsmodellen; det sies eksplisitt at observert tilgang brukes som inngang |
| Kryssystem-kontroll | Odometerbasert aktivitet × intensitet mot salgsstatistikk (uavhengige målesystemer) | Sterkeste reelle eksterne kontroll som finnes i kildebildet |
| Energibalanse-avstemming | Modellert el mot post 12.2.1 (2 783 GWh i 2024); bensin mot salget, ikke EB-posten (jf. pkt. 4) | Delvis uavhengig; metodegrense navngitt |
| Konsistens 12577/07849 | Implisitt antall mot 31.12-bestand | Utført i fase 0 (pkt. 8.3); blir løpende kontroll |
| Reproduksjonskontroll | Sammenligning mot Drivkraft Norges publiserte tall | Samme SSB-grunnlag (verifisert på deres side); omtales aldri som uavhengig validering |
| Sensitivitet/Monte Carlo | Parametervariasjon innen scenario | Fase 5 |
| Scenarioinvarians | Identiteter og ikke-negativitet holder i alle baner | Fase 5 |

## 11. Konklusjon

**GO**, med følgende presiseringer som inngår i anbefalingen: (1) autodieselserien segmenteres ved 2020-bruddet og skjøtes ikke; (2) den gjennomgående månedsserien bygges på petroleumsmåltallet, med rent bio som tilleggsserie fra 2022; (3) kjernen er personbiler, varebiler er sekundærmodul, tunge kjøretøy bare avstemming; (4) elektrisitet publiseres som modellert størrelse med navngitt valideringsgrense; (5) prognosemodul utelates (kriteriesvikt dokumentert i `02_method_decision.md`); (6) energitall for flytende drivstoff holdes ute av offentlige hovedtall til brennverdikilden er lest og verifisert (fase 1).

Hovedproblemstillingen står, med én presisering av ordlyden: «den norske kjøretøyparken» erstattes av «den norske personbilparken (med varebiler som utvidelse)», og «fram mot 2035» realiseres som betingede scenarioer, ikke prognoser.

### Anbefalt reponavn

Anbefaling: **`veitransport-energi`** – kort, presist, norsk som innholdet og konsistent med porteføljens eksisterende navnestil; engelsk repo-beskrivelse ivaretar søkbarhet. Alternativer vurdert: `transport-energy-norway` (arbeidsnavnet; bredere enn innholdet og engelsk mens produktet er norsk), `road-transport-energy-norway` (presis, men lang), `kjoretoypark-energi` (mister transportkonteksten). Navnevalget er prosjekteiers beslutning før repoopprettelse.

### Åpne beslutninger som krever prosjekteiers godkjenning

1. Endelig hovedestimand som formulert i charterets pkt. 2.
2. Scope-presiseringene (1)–(6) over, særlig utelatt prognosemodul.
3. Reponavn.
4. Om varebilmodulen skal med i første offentlige versjon eller legges til i en senere release.
