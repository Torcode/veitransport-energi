# Scenariodesign — fase 5

Dokumentet fastsetter hva scenarioene i fase 5 betinger på, hva de kan uttale
seg om, og hvor grensen går. Beslutningen er ført som D-0032. Alle tall som
siteres, er hentet fra artefaktene og kontrollert av tester; ingen av dem er
skrevet inn for hånd.

## 1. Utgangspunktet er et annet enn litteraturen forutsetter

Den vanlige framgangsmåten i norske omstillingsanalyser er å betinge på
elbilandelen i nyregistreringer: hva skjer med drivstoffetterspørselen dersom
andelen når 80, 90 eller 100 prosent? Den spaken er nå i praksis brukt opp.

Elandelen av nyregistrerte personbiler var **94,8 prosent i 2025**, opp fra 42,5
i 2019. Bensin og diesel utgjorde til sammen 2,2 prosent. Forskjellen mellom et
scenario med 95 prosent og ett med 100 prosent er dermed to prosent av
nyregistreringene i én årgang — et bidrag som drukner i alt annet som er usikkert.

Det som er åpent, ligger et annet sted:

**Hvor fort forlater den eksisterende fossile parken veien?** Kohortmodellen
identifiserer levetidsnivået godt, men ikke formen på avgangskurven: over
rullerende estimeringsvinduer flytter skalaen seg 4–10 prosent, formen 40–45
(`control_survival_parameter_stability.csv`, D-0028). Og det er formen en
framskriving er følsom for.

**Hvor mye kjøres de fossile bilene som er igjen?** Kjørelengden per bensinbil
har falt fra 10 160 til 8 060 km i året siden 2016, per dieselbil fra 15 430 til
12 420. Elbilene har gått motsatt vei, fra 11 910 til 13 530. Å anta konstant
kjørelengde per kjøretøy — det vanlige — ville overvurdert fossil etterspørsel
systematisk.

**Hva er sammensetningen av det som blir igjen?** En dieselbil kjøres 54 prosent
lenger enn en bensinbil. Hvilken av dem som forlater parken først, betyr derfor
mer for drivstoffetterspørselen enn antallet alene tilsier.

## 2. Hva estimandet dekker — og hva det ikke dekker

Modellen omfatter person- og varebiler. Andelen av hver energibærers kjørte
kilometer som ligger innenfor den avgrensningen, er beregnet i
`control_estimand_coverage.csv`:

| Energibærer | Personbiler | Varebiler | Innenfor estimandet | 2025 |
|---|---|---|---|---|
| Bensin | 97,8 % | 2,0 % | **99,8 %** | nær fullstendig |
| Elektrisitet | 91,7 % | 4,0 % | **95,7 %** | fallende, tyngre kjøretøy elektrifiseres |
| Autodiesel | 55,1 % | 30,9 % | **86,0 %** | og andelen faller |

Asymmetrien avgjør hva scenarioene har lov til å påstå.

For **bensin** er etterspørselen i praksis en personbilhistorie. En framskriving
av personbilparkens bensinforbruk er en framskriving av bensinetterspørselen.

For **elektrisitet** dekkes det meste, men dekningen faller — fra 99,8 prosent i
2015 til 95,7 i 2025 — fordi tunge kjøretøy elektrifiseres. Framskrivingen
gjelder person- og varebilers elforbruk, ikke veitransportens samlede.

For **autodiesel** går det ikke. Bare 86 prosent av dieselkilometerne ligger
innenfor estimandet, og andelen faller. Verre: tallet er *kilometer*, ikke
volum. Et vogntog bruker flere ganger så mye diesel per kilometer som en
personbil, så andelen av dieselvolumet innenfor estimandet er lavere enn 86
prosent.

> **Korreksjon 2026-08-12 (D-0033).** Setningen over fortsatte opprinnelig med at
> «hvor mye lavere, kan ikke avgjøres fra prosjektets kilder». Det var for raskt.
> Utslippsregnskapet (SSB-tabell 13931) fører CO2 fra veitrafikk delt på
> kjøretøygruppe og energivare, og siden CO2 per liter er en egenskap ved
> drivstoffet og ikke ved kjøretøyet, *er* forholdstallene mellom gruppene
> volumandeler. Fordelingen er dermed observerbar uten at noen utslippsfaktor må
> antas. Tallene står i `control_fuel_volume_shares.csv` og
> `control_volume_vs_distance.csv`, og avsnittet under erstatter det som ble
> strøket.


### Volumandelene, målt

| Energibærer (2024) | Andel av kilometer innenfor estimandet | Andel av volum innenfor estimandet | Differanse |
|---|---|---|---|
| Bensin | 99,8 % | 91,8 % | 8,0 pp |
| Autodiesel | 86,3 % | 55,1 % | 31,2 pp |

Bensinens differanse er motorsykler og mopeder, som står for 8,0 prosent av
bensinvolumet og ikke inngår i estimandet. Dieselens differanse er tunge
kjøretøy: de kjører 13,7 prosent av dieselkilometerne, men bruker 44,9 prosent av
dieselen. Personbilene alene kjører 56,3 prosent av dieselkilometerne og bruker
33,0 prosent av volumet.

Konsekvensen for leveransen er skarpere enn før, ikke svakere. Prosjektet kan nå
tallfeste hvor stor del av hver energibærer det dekker, framfor å måtte si at
grensen ikke lar seg fastsette. Men konklusjonen står: person- og varebiler er
drøyt halvparten av autodieselvolumet, så en framskriving for disse gruppene er
ikke en framskriving av autodieselsalget.

**Konsekvens:** fase 5 framskriver person- og varebilers dieselforbruk, aldri
totalt autodieselsalg. Resultatfiler og figurer skal si det i navnet, ikke i en
fotnote. En leser som tar personbildelen for totalen, vil undervurdere
etterspørselen kraftig, og produktet skal gjøre den feilen vanskelig å gjøre.

## 3. Scenarioene

Fire baner, hver betinget på navngitte parametre fra antakelsesregisteret. Ingen
av dem er «mest sannsynlig», og de har ingen sannsynlighet knyttet til seg.
Betegnelsen er **scenario** i prosjektets begrepsdisiplin: en betinget beregning
av hva som følger dersom de oppgitte forutsetningene holder.

**S0 Referansebane.** Alle parametre på registerets sentralverdier, tilgang av
nye kjøretøy holdt på gjennomsnittet av de siste tre observerte årene,
kjørelengde per kjøretøy videreført med den observerte trenden per drivlinje.
Banen er et *referansepunkt å måle de andre mot*, ikke et anslag på hva som vil
skje.

**S1 Rask utfasing.** Overlevelsesparametrene i nedre ende av spennet fra
reestimering, og fortsatt fall i kjørelengde per fossilt kjøretøy. Svarer på:
hvor tidlig kan bensinetterspørselen være borte dersom parken tømmes i det
raskeste tempoet dataene tåler?

**S2 Treg utfasing.** Motsatt: overlevelsesparametrene i øvre ende, og
kjørelengde per fossilt kjøretøy stabilisert på dagens nivå. Svarer på: hvor lenge
kan en restetterspørsel bli stående?

**S3 Aktivitetsnivå.** Samme utfasing som S0, men samlet trafikkarbeid varieres.
Skiller virkningen av *hvor mange og hvilke biler* fra virkningen av *hvor mye de
kjøres* — to mekanismer som ellers blandes sammen i ett tall.

Spennet mellom S1 og S2 er et **scenariospenn**, ikke et prediksjonsintervall, og
skal aldri tegnes som et konfidensbånd.

## 4. Usikkerhet holdes typedelt

D-0009 fastsatte at usikkerhet ikke skal slås sammen til ett bånd uten at
innholdet er definert. Det følges her:

| Type | Behandling |
|---|---|
| Datamåling og revisjon | vintage i manifestet; revisjonssensitivitet vises separat |
| Parameterusikkerhet | Monte Carlo *innenfor* hvert scenario, over registerets spenn |
| Spesifikasjonsusikkerhet | rate-modellen beholdt som alternativ spesifikasjon å måle mot |
| Scenariousikkerhet | atskilte baner, aldri slått sammen |

Parameterusikkerheten trekkes fra antakelsesregisterets spenn, som for
overlevelsesparametrene er reestimering på rullerende vinduer — ikke profilering
av tilpasningen, som ville gitt falsk presisjon (D-0028).

Sensitivitetsrangeringen skal svare på ett spørsmål eksplisitt: hvilken enkelt
antakelse flytter resultatet mest? Etter det som er dokumentert så langt, er
kandidaten formen på overlevelseskurven for elbiler, der en teknisk framskriving
til 2035 spente fra −20 til +29 prosent på skalaen alene.

## 5. Hva som må bygges før scenarioene kan kjøres

1. **Kjørelengde per kjøretøy som modellert størrelse.** I dag er den observert
   og faller systematisk for fossile biler. Trenden må modelleres og føres i
   antakelsesregisteret med spenn, ikke antas konstant.
2. **Energiintensitet per kjøretøygruppe.** Den kalibrerte intensiteten gjelder
   hele veitransporten under ett. Per gruppe må den komme utenfra, med
   dokumentert kilde og spenn — som utility factor, og med samme forbehold.
3. **Kohortmodell for varebiler.** Bygget og validert for personbiler; varebiler
   står for 30,9 prosent av dieselkilometerne og kan ikke utelates.

Punkt 2 er det som avgjør om fase 5 kan levere liter og TWh, eller bare
kjøretøykilometer per drivlinje. Om ingen defensibel kilde finnes, leveres
kilometerne, og energiomregningen står som en navngitt kunnskapsgrense framfor en
antakelse resultatet ikke tåler.
