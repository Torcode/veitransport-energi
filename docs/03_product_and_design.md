# Produkt og visuelt konsept (fase 0)

Dato: 2026-08-10. Dokumentet fastlegger brukerreise, informasjonsrekkefølge og et foreløpig designsystem for README, GitHub Pages og dokumentleveransene. Endelige detaljvalg gjøres mot rendret innhold i fase 6, men prinsippene her er bindende arbeidsgrunnlag.

## 1. Brukerreisen

**Inngang 1 – repoets forside (nivå 1, ca. ett minutt).** README åpner med: problemsetning (to setninger), hovedfiguren (statisk PNG/SVG av de tre energibanene, historisk og scenario), tre–fem hovedtall med vintage-merking, én metodesetning, én begrensningssetning, og to tydelige lenker: «Beslutningsflate» og «Full dokumentasjon». Deretter kort navigasjonstabell til nivå 3-innholdet. Ingen badge uten at den beviser noe reelt; badge-tekst skal samsvare med det workflowen faktisk kjører.

**Inngang 2 – beslutningsflaten (nivå 2).** GitHub Pages, én side, leserekkefølge ovenfra: (1) hovedfunn i én setning med vintage; (2) hovedfiguren interaktiv (scenariovelger); (3) driverpanel – nyregistrering, bestand, kjørelengde, intensitet; (4) forutsetningstabell for valgt scenario med status per antakelse; (5) usikkerhetsseksjon (hva spennet er – og hva det ikke er); (6) kilder, vintage, lisens, kjente begrensninger. Siden leser utelukkende versjonerte resultatfiler (`artifacts/`); ingen beregning i JavaScript utover presentasjon; statisk tabellfallback for alle interaktive elementer (tastatur- og mobiltilgjengelig).

**Inngang 3 – etterprøving (nivå 3).** Metodenote, kilderegister, kodebok, antakelsesregister, valideringsresultater, beslutningslogg, kode og tester, alle lenket fra README-navigasjonen. En leser skal kunne gå fra ethvert hovedtall til artefaktfil, derfra til produserende kode og derfra til kilde-URL uten blindveier.

## 2. Hva som er synlig først

Prioritert rekkefølge for førstevisningen (README og Pages): (1) de tre energibanene samlet – bensin, autodiesel, elektrisitet – historisk og fram mot 2035; (2) elandelen i bestand og nyregistrering; (3) scenariospennet for elektrisitetsbehov i 2035; (4) fallet i bensin/autodiesel siden toppåret. Alt annet (dekomponering, avstemming, sensitivitet) ligger ett klikk/scroll ned. Begrunnelse: hovedspørsmålet i charteret besvares av figur 1; resten er begrunnelse og kontroll.

## 3. Konvensjoner for tallenes status

Gjennomgående, i figurer, tabeller og tekst:

| Status | Konvensjon i figur | Konvensjon i tabell/CSV |
|---|---|---|
| Observert | Heltrukket linje, fylt markør | `observert` |
| Konstruert fra observerte data (skjøtt/aggregert) | Heltrukket, åpen markør + fotnote | `konstruert` |
| Estimert/kalibrert | Stiplet linje | `estimert`/`kalibrert` |
| Scenarioforutsatt | Tynn linje i vifte, scenarioetikett direkte på linjen | `scenarioforutsatt` |
| Brudd | Vertikal grå linje med kort tekst («brudd 2020: innsamlingskorreksjon») | egen bruddkolonne i serien |

Usikkerhet: bånd tegnes bare når dokumentet kan si presist hva båndet representerer (scenariospenn eller MC-fordeling innen scenario – aldri omtalt som prognoseintervall). Fargefylte bånd med lav dekkraft, aldri flere overlappende bånd uten interaksjon.

## 4. Foreløpig designsystem

- **Typografi:** systemnær sans (`system-ui`-stakk) for alt; tabelltall med `font-variant-numeric: tabular-nums`. Ingen webfont-avhengighet i første versjon (ytelse og enkelhet); revurderes mot rendret resultat i fase 6.
- **Farger (Okabe–Ito-avledet, fargeblindtrygg):** bensin `#E69F00` (oransje), autodiesel `#D55E00` (rødbrun), elektrisitet `#0072B2` (blå), bio/øvrig `#009E73` (grønn), kontekst/historikk-hjelpelinjer i grå (`#666`, `#999`). Serieidentitet bæres aldri av farge alene: direkte etiketter på linjene, ulik markørform per bærer. Tekst/bakgrunn-kontrast minst 4,5:1; interaktive elementer minst 3:1 mot naboflater.
- **Flater og avstander:** hvit bakgrunn, maks tekstbredde ca. 70 tegn, 8 px-basert avstandsskala, kort («cards») bare for hovedtallpanelet – ellers rolig dokumentflyt. Tabeller venstrestilles, tallkolonner høyrestilles, tusenskille med smalt mellomrom, desimalkomma i norsk tekst.
- **Figurstandard:** akser uten unødig ramme, ingen gridlinjer tettere enn nødvendig, kildelinje + vintage nederst i hver figur («Kilde: SSB 13585, uttrekk 2026-08-10 · brudd markert»), samme marger og fonthierarki i alle figurer, y-akse fra null for volum/energi (avvik begrunnes i figurteksten). Hver figur følges av tekst som sier hva den viser, hvorfor den er relevant, hvordan dataene produserer mønsteret og hvilke begrensninger som gjelder – uten unntak.
- **Responsivt:** énkolonne under 700 px; figurer skalerer med `max-width`; tabeller får horisontal rulling med frosset førstekolonne; interaktive kontroller har `<noscript>`-/statisk fallback. Testmatrisen fra prosjektbeskrivelsen (desktop, smal mobil, README-rendering, Pages, tabellbredder, akseetiketter, lenker, kontrast, tomme/ekstreme tilstander) kjøres visuelt før hver PR i fase 6 regnes som ferdig.

## 5. Avgrensning mot porteføljens eksisterende prosjekt

Produktet skal kjennes igjen som noe annet enn bostøtteprosjektet på tre målbare punkter: (1) egen fargeidentitet (bærerpaletten over) og egen forsidestruktur (hovedfigur + driverpanel, ikke horisontvelger som bærende interaksjon); (2) hovedinteraksjonen er scenariovalg mellom betingede baner, ikke prognosehorisont; (3) fortellingens enhet er årlige mekanismer (bestand → aktivitet → energi), ikke månedlig prediksjonsevaluering. Gjenbruk av generiske tekniske prinsipper (datakontrakter, versjonerte artefakter, CI-disiplin) er tilsiktet; prosa, dramaturgi og sidestruktur skrives fra dette prosjektets behov.

## 6. Unngås bevisst

Generisk dashbord-estetikk og pynteelementer uten analytisk funksjon; gradienter og dekorativ animasjon; mer enn fire serier i samme panel uten interaksjon; «presise» figurer uten usikkerhets- eller statusmarkering; fargekoding som eneste bærer av mening; visuell etterligning av offentlige etaters eller mulige arbeidsgiveres profil; skjermfyllende hero-seksjoner. Sosial forhåndsvisning (OG-bilde) lages som forenklet utgave av hovedfiguren med tittel – ingen dekorillustrasjon.

## 7. Dokumentmaler

Rådgivernotatet (1–2 sider): beslutningsproblem → hovedfunn (tre punkter med tall og vintage) → drivere → usikkerhet → implikasjoner → overvåkingsliste → «dette gir analysen ikke grunnlag for å hevde». Metodenoten følger strukturen estimand → data → koblinger → modell → antakelser → validering → usikkerhet → sensitivitet → begrensninger, så lang som nødvendig og ikke lenger. Begge produseres fra samme artefaktfiler som beslutningsflaten; ingen hovedtall skrives manuelt.
