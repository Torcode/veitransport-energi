# Beslutningslogg

Format per post: dato · beslutning · alternativer vurdert · valgt løsning · begrunnelse · evidensgrunnlag · konsekvens · opphav og status. Poster med status «foreslått» er ikke bindende før prosjekteier har godkjent dem. Der prosjekteier overprøver en anbefaling, føres det som egen post.

---

**D-0001 · 2026-08-10 · Rammeverk for fase 0**
Prosjektbeskrivelsens rammer (faseinndeling, verifikasjonskontrakt, kildehierarki, begrepsdisiplin, main som releasegren, ingen offentlig repo før godkjent fase 0) legges til grunn uendret. Alternativer: ingen. Evidens: prosjektbeskrivelsen. Konsekvens: styrer alle øvrige poster. **Opphav: prosjekteier. Status: vedtatt.**

**D-0002 · 2026-08-10 · Skjøtestrategi for salgsserien**
Alternativer: (a) én lang, nivåjustert serie 1995–2026; (b) segmentert publisering med definert gjennomgående måltall og synlige brudd. Valgt: (b), med petroleumsmåltallet (inkl. iblandet bio) som gjennomgående begrep 2010M01–2026M06, og bensin/dieselsum tilbake til 1995 som egne segmenter. Begrunnelse: (a) ville skjule det dokumenterte 2020-bruddet og bryte verifikasjonskontraktens punkt 5. Evidens: skjøtetestene (bensin medianavvik 0,0 %, dieselsum 0,0 %; petroleumsmåltall identisk i 2022M01) og SSBs bruddnoter; `analysis/design_gate/results/`. Konsekvens: nivåendringer over 2020 tolkes aldri for autodiesel; serier får bruddmetadata. **Opphav: foreslått av KI-assistenten. Status: foreslått.**

**D-0003 · 2026-08-10 · Autodiesel før 2010**
Alternativer: (a) forlenge autodiesel bakover med antatt fordeling av gammel «Diesel»; (b) publisere kun dieselsum før 2010. Valgt: (b). Begrunnelse: autodiesel alene ligger i snitt 24 % under gamle «Diesel»; en fordelingsantakelse ville skape en kunstig presis serie. Evidens: skjøtetest A (mean_ratio 0,763). Konsekvens: autodieselserien starter 2010. **Opphav: foreslått av KI-assistenten. Status: foreslått.**

**D-0004 · 2026-08-10 · Kjerneavgrensning kjøretøy**
Alternativer: (a) personbiler; (b) personbiler + varebiler; (c) hele veitransporten. Valgt: (a) som kjerne, (b) som sekundærmodul etter koblingskontroll, (c) kun som avstemmingslag. Begrunnelse: personbiler har komplette ledd med drivlinjedeling; diesel kan uansett bare avstemmes på veitransportnivå; restposter skal være synlige, ikke skjulte. Evidens: datamatrisen og EB-diagnostikken (implisitt brennverdi bensin 22,6–24,6 MJ/l viser vesentlig allokering utenfor vei). Konsekvens: estimandet gjelder personbiler; avstemming skjer bredere. **Opphav: foreslått av KI-assistenten. Status: foreslått.**

**D-0005 · 2026-08-10 · Frekvens**
Alternativer: månedlig hovedmodell; årlig hovedmodell; flerfrekvent produkt. Valgt: årlig modell, månedlig segmentert statistikkserie. Begrunnelse: bestand/kjørelengde/energibalanse er årlige; månedsdynamikk tilfører ikke identifikasjon for estimandet. Evidens: metadataene (tabellfrekvenser). Konsekvens: scenarioer og dekomponering på årsbasis. **Opphav: foreslått av KI-assistenten. Status: foreslått.**

**D-0006 · 2026-08-10 · Energiidentitet på aktivitetsbasis**
Alternativer: (a) energi = bestand × km/kjøretøy × intensitet i alle ledd; (b) historisk energi = observert total-km × intensitet, med bestandsleddet kun for framskriving. Valgt: (b). Begrunnelse: total kjørelengde er direkte observert 2005–2025; å gå veien om bestand × gjennomsnitt ville importere et definisjonsavvik (4–16 % målt) uten gevinst. Evidens: 12577-uttrekket og konsistenskontrollen mot 07849. Konsekvens: færre konstruerte ledd historisk; bestand–strøm-modellen bærer bare framtidsdelen. **Opphav: foreslått av KI-assistenten. Status: foreslått.**

**D-0007 · 2026-08-10 · Nettoavgang**
Alternativer: (a) kalle residualen «vraking»; (b) «nettoavgang» som residual med eksplisitt innhold (vraking, eksport, avregistrering, omklassifisering); (c) overlevelsesmodell fra start. Valgt: (b), med (c) som betinget utvidelse i fase 3 hvis aldersdataene identifiserer overlevelse bedre. Begrunnelse: ingen eksportstatistikk i kildebildet; enklere løsning gir samme validerbarhet nå. Evidens: kildekartleggingen; 12575/12578 identifisert for ev. utvidelse. Konsekvens: ingen levetidstolkning av residualen. **Opphav: foreslått av KI-assistenten. Status: foreslått.**

**D-0008 · 2026-08-10 · Prognosemodul**
Alternativer: (a) inkludere månedlig prognosemodul; (b) utelate; (c) utsette. Valgt: (b) NEI. Begrunnelse: publiseringslag ca. tre uker gir minimal nåkast-verdi; ingen definert operativ bruker; dupliserer porteføljens demonstrerte format uten å tilføre beslutningsverdi; kriteriene 1 og 5–6 i metodeporten feiler. Evidens: SSBs publiseringskalenderomtale (verifisert på statistikksiden) og `02_method_decision.md` M4. Konsekvens: `forecast_results.csv` utgår fra leveranselisten; framtidsdelen er scenariobasert. **Opphav: foreslått av KI-assistenten. Status: foreslått – krever prosjekteiers beslutning.**

**D-0009 · 2026-08-10 · Usikkerhetsarkitektur**
Alternativer: samlet usikkerhetsbånd; typedelt usikkerhet. Valgt: typedelt (datamåling/revisjon, parameter, spesifikasjon, scenario) med Monte Carlo innen scenario og sensitivitetsrangering; ingen sammenslåing uten eksplisitt forklaring. Begrunnelse: scenariospenn og parameterusikkerhet svarer på ulike spørsmål; sammenslåing ville gi et bånd uten definert innhold. Evidens: prosjektbeskrivelsens krav + M6. Konsekvens: figurkonvensjoner i `03_product_and_design.md`. **Opphav: foreslått av KI-assistenten. Status: foreslått.**

**D-0010 · 2026-08-10 · Elektrisitet som modellert størrelse**
Alternativer: (a) presentere energibalansens el-post som fasit; (b) publisere modellert el med EB-posten som delvis uavhengig avstemming og navngitt metodegrense. Valgt: (b). Begrunnelse: EBs fordelingsmetode for el til veitransport er ikke dokumentert i det som er hentet; uavhengigheten er uavklart. Evidens: «Om statistikken»-henting for energibalansen (fordelingsmetode ikke beskrevet der). Konsekvens: valideringsspråket sier «avstemming», ikke «validering», for el inntil metoden er avklart i fase 1–2. **Opphav: foreslått av KI-assistenten. Status: foreslått.**

**D-0011 · 2026-08-10 · Brennverdier holdes ute til verifisert**
Alternativer: (a) bruke typiske litteraturverdier nå; (b) holde energitall for flytende drivstoff ute av offentlige hovedtall til SSB Notater 2018/45 vedlegg A er lest. Valgt: (b). Begrunnelse: verifikasjonskontraktens punkt 1; kilden er identifisert, lesing er en billig fase 1-oppgave. Evidens: energibalansens «Om statistikken» peker eksplisitt på notatets vedlegg A; PDF-henting feilet i fase 0 (404 på ett vedleggsforsøk). Konsekvens: fase 0-dokumentene oppgir ingen brennverditall som fakta; unit_map merker faktorene «ikke verifisert». **Opphav: foreslått av KI-assistenten. Status: foreslått.**

**D-0012 · 2026-08-10 · Drivkraft Norge og NOBIL**
Beslutning: Drivkraft Norge-sammenligning klassifiseres som reproduksjonskontroll (siden oppgir selv SSB som kilde – verifisert sitat); NOBIL utelates fra kjernen (verifisert: «NOBIL har dessverre ingen historisk funksjon»). Alternativer: omtale som uavhengig validering / bygge historikk fra Created-tidsstempler. Forkastet pga. felles kildegrunnlag hhv. survivorship-skjevhet. Evidens: hentede sider (URL-er i kilderegisteret). Konsekvens: valideringsdesignets språkbruk; ladeinfrastruktur utenfor scope. **Opphav: foreslått av KI-assistenten. Status: foreslått.**

**D-0013 · 2026-08-10 · Teknisk plattform og API-praksis**
Beslutning: Python-first bekreftes (ingen bedre løsning dokumentert); alle SSB-uttrekk går via PxWebAPI v2-beta med eksplisitte valueCodes for alle dimensjoner, lokal cache og maskinell forespørselslogg (`request_log.csv`). Evidens: fungerende fase 0-skript; API-kravet (400 uten alle valueCodes) bekreftet i praksis ved at alle kall spesifiserte dimensjonene eksplisitt. Konsekvens: reproduserbare uttrekk fra fase 1. **Opphav: foreslått av KI-assistenten. Status: foreslått (reversibelt teknisk valg).**

**D-0014 · 2026-08-10 · Reponavn**
Alternativer: `transport-energy-norway` (arbeidsnavn), `road-transport-energy-norway`, `veitransport-energi`, `kjoretoypark-energi`. Anbefalt: `veitransport-energi`. Begrunnelse: samsvar mellom navn, innholdsspråk og porteføljens navnestil; presist scope. Evidens: `01_design_gate.md` pkt. 11. Konsekvens: settes ved repoopprettelse i fase 1. **Opphav: foreslått av KI-assistenten. Status: åpen – prosjekteiers beslutning.**

**D-0015 · 2026-08-10 · Fylkesdimensjonen ut av kjernen**
Beslutning: ingen fylkesfordelte hovedserier. Alternativer: regional modul basert på 03687/11174 (til 2022). Forkastet i kjernen fordi 13585 mangler fylke og regionkodenes stabilitet gjennom 2020-reformen er uverifisert. Evidens: metadata (dimensjonslister). Konsekvens: nasjonalt hovedprodukt; regional deskriptiv bruk kan vurderes i fase 2 med egen kontroll. **Opphav: foreslått av KI-assistenten. Status: foreslått.**
