# Figurer bygget utelukkende fra publiserte artefakter.
#
# Ingen av tallene under regnes ut her. Alt som tegnes, finnes allerede i
# artifacts/, og koden filtrerer, summerer over måneder til år og pivoterer for
# framstilling. Skillet er ikke pedantisk: så snart en figur regner ut sitt eget
# hovedtall, har prosjektet to sannheter, og verifikasjonskontrakten forbyr det.

suppressPackageStartupMessages({
  library(dplyr)
  library(tidyr)
  library(ggplot2)
  library(scales)
})

#' Årssum av en månedsserie, bare for år med tolv observerte måneder.
#'
#' Delvise år ville gitt et fall i siste punkt som ser ut som et funn og bare er
#' manglende måneder.
aarssum_hele_aar <- function(d) {
  d %>%
    mutate(aar = as.integer(substr(periode, 1, 4))) %>%
    group_by(serie_id, gruppe, drivlinje, variabel, enhet, segment, aar) %>%
    summarise(verdi = sum(verdi), maaneder = dplyr::n(), .groups = "drop") %>%
    filter(maaneder == 12)
}

#' Figur 1: salget av bensin og autodiesel, med bruddet synlig framfor utglattet.
#'
#' Bensinserien er skjøtt over tre kilder fordi skjøtene er empirisk testet i
#' overlappsmånedene. Autodieselserien er det ikke: innsamlingen ble lagt om i
#' 2020, og de to segmentene tegnes derfor som atskilte linjer med et hull. Hullet
#' er figurens viktigste egenskap.
figur_salg_segmentert <- function(hist, prov) {
  d <- hist %>%
    filter(variabel == "salgsvolum", frekvens == "M") %>%
    aarssum_hele_aar() %>%
    mutate(
      serie = case_when(
        drivlinje == "bensin" ~ "bensin",
        segment == "autodiesel_2020_" ~ "autodiesel (fra 2020)",
        segment == "autodiesel_2010_2019" ~ "autodiesel (2010-2019)",
        TRUE ~ NA_character_
      ),
      farge = if_else(drivlinje == "bensin", "bensin", "autodiesel")
    ) %>%
    filter(!is.na(serie), aar >= 2010)

  # Direkte etiketter framfor tegnforklaring. Den avsluttede autodieselserien
  # merkes midt på sin egen linje; ved enden ville den lagt seg oppå segmentet
  # som starter i 2020, og en etikett som peker på feil linje er verre enn ingen.
  etiketter <- bind_rows(
    d %>% filter(serie == "autodiesel (2010-2019)") %>% filter(aar == 2011) %>%
      mutate(hj = 0, vj = 2.0),
    d %>% filter(serie != "autodiesel (2010-2019)") %>% group_by(serie) %>%
      slice_max(aar, n = 1) %>% ungroup() %>% mutate(hj = 0, vj = 0.4)
  )

  ggplot(d, aes(aar, verdi, colour = farge, group = serie)) +
    annotate("segment", x = 2019.5, xend = 2019.5, y = 0, yend = 3250,
             colour = FARGER[["hjelpelinje"]], linetype = "dotted", linewidth = 0.4) +
    annotate("text", x = 2019.4, y = 250, label = "innsamlingsbrudd 2020",
             hjust = 1, size = 3, colour = FARGER[["ovrig"]]) +
    geom_line(linewidth = 0.8) +
    geom_point(aes(shape = farge), size = 1.6) +
    geom_text(data = etiketter, aes(label = serie, hjust = hj, vjust = vj),
              nudge_x = 0.2, size = 3.1, show.legend = FALSE) +
    skala_drivlinje() +
    scale_shape_manual(values = c(bensin = 16, autodiesel = 17)) +
    scale_y_continuous(limits = c(0, NA), labels = label_number(big.mark = " ")) +
    scale_x_continuous(breaks = seq(2010, 2025, 5), limits = c(2010, 2029.5)) +
    labs(
      title = "Salget av bensin og autodiesel faller, men kildene tåler ikke én linje",
      subtitle = "Millioner liter per år. Autodieselserien er delt ved innsamlingsbruddet i 2020",
      x = NULL, y = "mill. liter",
      caption = kildelinje(c("03687", "11174", "13585"), prov,
                           tillegg = "brudd i autodiesel 2020 vist som avbrudd, ikke skjøtt")
    ) +
    tema_veitransport()
}

#' Figur 2: elbilenes andel av bestanden mot andelen av kjørte kilometer.
#'
#' De to kurvene besvarer ulike spørsmål. Bestandsandelen sier hvor mange biler
#' som er elektriske; kjørelengdeandelen sier hvor stor del av trafikkarbeidet de
#' utfører — og det er sistnevnte som fortrenger drivstoff.
figur_andel_bestand_mot_kjorelengde <- function(hist, prov) {
  andel <- function(var, navn) {
    hist %>%
      filter(variabel == var, gruppe == "personbiler") %>%
      group_by(periode) %>%
      summarise(andel = sum(verdi[drivlinje == "elektrisitet"]) / sum(verdi) * 100,
                .groups = "drop") %>%
      mutate(aar = as.integer(substr(periode, 1, 4)), maal = navn)
  }
  d <- bind_rows(andel("bestand_3112", "andel av bestanden"),
                 andel("kjorelengde_total", "andel av kjørte km")) %>%
    filter(aar >= 2010)
  etiketter <- d %>% group_by(maal) %>% slice_max(aar, n = 1) %>% ungroup()

  ggplot(d, aes(aar, andel, group = maal)) +
    geom_line(aes(linetype = maal), colour = FARGER[["elektrisitet"]], linewidth = 0.8) +
    geom_point(aes(shape = maal), colour = FARGER[["elektrisitet"]], size = 1.6) +
    geom_text(data = etiketter, aes(label = maal), hjust = 0, nudge_x = 0.25,
              size = 3.1, colour = FARGER[["elektrisitet"]]) +
    scale_linetype_manual(values = c("andel av bestanden" = "dashed",
                                     "andel av kjørte km" = "solid")) +
    scale_shape_manual(values = c("andel av bestanden" = 1, "andel av kjørte km" = 16)) +
    scale_y_continuous(limits = c(0, NA), labels = label_number(suffix = " %")) +
    scale_x_continuous(breaks = seq(2010, 2025, 5), limits = c(2010, 2030.5)) +
    labs(
      title = "Elbilene kjører mer enn resten av parken, ikke mindre",
      subtitle = "Personbiler. Andelen av trafikkarbeidet ligger over andelen av bestanden",
      x = NULL, y = "prosent",
      caption = kildelinje(c("07849", "12577"), prov,
                           tillegg = "bestand per 31.12, kjørelengde odometerbasert")
    ) +
    tema_veitransport()
}

#' Figur 3: de tre energibanene.
#'
#' Designdokumentets figur 1 — den eneste figuren som viser leveransen framfor et
#' enkeltfunn. Tallene er energibalansens produktposter for veitransport, som er
#' den ene av de to målesystemene prosjektet avstemmer mot hverandre; summen av
#' bensin og autodiesel er identisk med `eb_fossil_PJ` i energiavstemmingen.
#'
#' Filtreringen på utility_factor er en avduplisering, ikke et valg: `energi_PJ`
#' er den samme størrelsen i begge variantene, siden utility factor bare virker på
#' nevneren i intensitetsberegningen. Uten filteret ville hvert år tegnet to
#' identiske punkter oppå hverandre.
figur_energibaner <- function(intens, prov) {
  navn <- c(bensin = "bensin", diesel = "autodiesel", elektrisitet = "elektrisitet")
  d <- intens %>%
    filter(utility_factor == 0) %>%
    mutate(aar = as.integer(as.character(periode)),
           serie = unname(navn[energibaerer]),
           farge = energibaerer,
           # Elektrisitetsposten er modellert av SSB og fordelingsmetoden er ikke
           # dokumentert i det som er hentet. Statuskonvensjonen i designdokumentet
           # § 3 krever stiplet linje for modellerte størrelser; her er det den
           # eneste markeringen som skiller den fra de to observerte.
           modellert = energibaerer == "elektrisitet") %>%
    arrange(aar)
  etiketter <- d %>% group_by(serie) %>% slice_max(aar, n = 1) %>% ungroup()

  ggplot(d, aes(aar, energi_PJ, colour = farge, group = serie)) +
    geom_line(aes(linetype = modellert), linewidth = 0.8) +
    geom_point(aes(shape = farge), size = 1.5) +
    geom_text(data = etiketter, aes(label = serie), hjust = 0, nudge_x = 0.4,
              size = 3.1, show.legend = FALSE) +
    skala_drivlinje() +
    scale_linetype_manual(values = c(`FALSE` = "solid", `TRUE` = "dashed")) +
    scale_shape_manual(values = c(bensin = 16, diesel = 17, elektrisitet = 15)) +
    scale_y_continuous(limits = c(0, NA), labels = label_number(big.mark = " ")) +
    scale_x_continuous(breaks = seq(2005, 2025, 5), limits = c(2005, 2032)) +
    labs(
      title = "Elektrisiteten er ennå mindre enn bensinen",
      subtitle = "Energi til veitransport, petajoule per år. Elektrisitet er modellert av SSB og tegnes stiplet",
      x = NULL, y = "PJ per år",
      caption = kildelinje(c("11561"), prov,
                           tillegg = "fossilpostene er ekskl. innblandet biodrivstoff")
    ) +
    tema_veitransport()
}

#' Figur 4: tilgang mot avgang i den fossile personbilparken.
#'
#' Hovedfunnet, tegnet. Begge linjene måler mot bestanden ved inngangen til året,
#' og bare derfor kan de leses mot hverandre: forholdet mellom to rater med samme
#' nevner er forholdet mellom antallene. Artefaktet bærer også raten mot
#' utgangsbestanden, som er den forsiden siterer — de to må ikke blandes i samme
#' figur.
#'
#' Serien begynner i 2019 fordi den detaljerte drivstoffklassifikasjonen i 12906
#' gjør det. Den grove tabellen rekker lenger tilbake, men fører fossilt i et
#' aggregat som ikke svarer til bestandstabellens koder (D-0036), og en figur som
#' blandet de to ville vist et forholdstall mellom to ulike variabler.
figur_fossil_tilgang_mot_avgang <- function(tilgang, prov) {
  d <- tilgang %>%
    filter(gruppe == "personbiler", drivlinje == "fossil_bensin_diesel",
           !is.na(avgangsrate_pct)) %>%
    mutate(aar = as.integer(as.character(periode))) %>%
    select(aar, inn = tilgang_pct_av_bestand_forrige, ut = avgangsrate_pct) %>%
    pivot_longer(c(inn, ut), names_to = "retning", values_to = "rate") %>%
    mutate(serie = if_else(retning == "inn", "tilgang inn i parken",
                           "avgang ut av parken"))
  etiketter <- d %>% group_by(serie) %>% slice_max(aar, n = 1) %>% ungroup()

  ggplot(d, aes(aar, rate, group = serie)) +
    geom_line(aes(colour = serie), linewidth = 0.8) +
    geom_point(aes(colour = serie, shape = serie), size = 1.7) +
    geom_text(data = etiketter, aes(label = serie, colour = serie), hjust = 0,
              nudge_x = 0.2, size = 3.1, show.legend = FALSE) +
    scale_colour_manual(values = c(`tilgang inn i parken` = FARGER[["elektrisitet"]],
                                   `avgang ut av parken` = FARGER[["autodiesel"]])) +
    scale_shape_manual(values = c(`tilgang inn i parken` = 16, `avgang ut av parken` = 17)) +
    scale_y_continuous(limits = c(0, NA), labels = label_number(suffix = " %")) +
    scale_x_continuous(breaks = seq(2019, 2025, 2), limits = c(2019, 2029.5)) +
    labs(
      title = "For hver fossile personbil som kommer inn, forlater 26 parken",
      subtitle = "Prosent av fossil personbilbestand ved inngangen til året. Tilgang er nye og bruktimporterte",
      x = NULL, y = NULL,
      caption = kildelinje(c("12906", "07849"), prov,
                           tillegg = "detaljert drivstoffklassifikasjon; avgang er residual (D-0007)")
    ) +
    tema_veitransport()
}

#' Figur 5: kilometerandel mot volumandel, per energibærer.
#'
#' Dieselparadokset. Flaten mellom linjene er hele poenget: for bensin ligger
#' kilometer og volum tett, for autodiesel gjør de ikke det, og gapet vokser.
#' Panelene er `facet_wrap` framfor to sammensatte plott — `patchwork` er ikke
#' blant pakkene CI installerer, og en figur som bare kan bygges lokalt, er ikke
#' en del av leveransen.
#'
#' De to linjene er ikke målt i samme kilde: kilometerandelen er observert i
#' kjørelengdestatistikken, volumandelen utledet av utslippsregnskapet, og
#' gruppene er ikke identisk avgrenset. Sammenstillingen er omtrentlig, og det
#' står i kildelinjen framfor bare i artefaktets merknadsfelt.
figur_km_mot_volum <- function(vol, prov) {
  panelnavn <- c(diesel = "autodiesel", bensin = "bensin")
  d <- vol %>%
    mutate(aar = as.integer(as.character(periode)),
           panel = factor(unname(panelnavn[energibaerer]),
                          levels = c("autodiesel", "bensin")))
  lang <- d %>%
    select(aar, panel, energibaerer,
           `andel av kjørte km` = andel_innenfor_estimandet_pct,
           `andel av volumet` = andel_innenfor_volum_pct) %>%
    pivot_longer(c(`andel av kjørte km`, `andel av volumet`),
                 names_to = "maal", values_to = "andel")
  # Etikettene settes bare i venstre panel. Med etiketter i begge kolliderer de i
  # bensinpanelet, der linjene ligger 8 prosentpoeng fra hverandre; panelene deler
  # linjetype, så én merking rekker for begge.
  etiketter <- lang %>%
    filter(panel == "autodiesel") %>%
    group_by(maal) %>% slice_max(aar, n = 1) %>% ungroup() %>%
    mutate(vj = if_else(maal == "andel av kjørte km", -1.1, 1.9))

  ggplot(lang, aes(aar, andel)) +
    geom_ribbon(data = d, inherit.aes = FALSE,
                aes(x = aar, ymin = andel_innenfor_volum_pct,
                    ymax = andel_innenfor_estimandet_pct, fill = energibaerer),
                alpha = 0.16) +
    geom_line(aes(colour = energibaerer, linetype = maal), linewidth = 0.8) +
    geom_point(aes(colour = energibaerer, shape = maal), size = 1.4) +
    geom_text(data = etiketter, aes(label = maal, colour = energibaerer, vjust = vj),
              hjust = 1, size = 2.9, show.legend = FALSE) +
    facet_wrap(~panel) +
    skala_drivlinje() +
    scale_fill_manual(values = FARGER) +
    scale_linetype_manual(values = c(`andel av kjørte km` = "solid",
                                     `andel av volumet` = "dashed")) +
    scale_shape_manual(values = c(`andel av kjørte km` = 16, `andel av volumet` = 1)) +
    scale_y_continuous(limits = c(0, 100), labels = label_number(suffix = " %")) +
    scale_x_continuous(breaks = seq(2005, 2025, 10), limits = c(2005, 2024)) +
    labs(
      title = "86 prosent av dieselkilometerne, 55 prosent av dieselen",
      subtitle = "Andel som ligger innenfor person- og varebiler, prosent. Gapet er drivstoffet tunge kjøretøy bruker",
      x = NULL, y = NULL,
      caption = kildelinje(c("12577", "13931"), prov,
                           tillegg = "km observert, volum utledet; gruppene ikke identisk avgrenset")
    ) +
    tema_veitransport() +
    theme(strip.text = element_text(face = "bold", hjust = 0))
}
