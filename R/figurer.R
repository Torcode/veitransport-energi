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
