# Designsystemet fra docs/03_product_and_design.md, uttrykt som ggplot-tema.
#
# Paletten er Okabe-Ito-avledet og fargeblindtrygg. Regelen fra designdokumentet
# gjelder også her: serieidentitet bæres aldri av farge alene — figurene skal ha
# direkte etiketter og ulik markørform, slik at de er lesbare i gråtoner og for
# den som ikke skiller rødbrunt fra oransje.

suppressPackageStartupMessages({
  library(ggplot2)
})

# Prøvestreng for tegnkontrollen. Den ligger her, i en UTF-8-kildefil med norske
# tegn, fordi det er nettopp kildeparsingen som svikter i feil locale — artefakter
# lest med readr er UTF-8-merket uansett og ville ikke avslørt noe. Ordet under er
# det som havner i figurtekst; blir det til «kj..relengde», skal broen ryke.
TEGNPROVE <- "kjørelengde og påvirkning"

FARGER <- c(
  bensin              = "#E69F00",
  autodiesel          = "#D55E00",
  diesel              = "#D55E00",
  elektrisitet        = "#0072B2",
  bio                 = "#009E73",
  hybrid_ladbar       = "#009E73",
  hybrid_ikke_ladbar  = "#56B4E9",
  ovrig               = "#666666",
  hjelpelinje         = "#999999"
)

#' Norsk tallformat: desimalkomma og smalt tusenskille.
#'
#' Designdokumentet krever det i norsk tekst, og R gjør det ikke selv — `format()`
#' følger locale, og prosjektet kjører med vilje i C.UTF-8 for at tegnbehandlingen
#' skal være lik overalt. Da må tallformatet settes eksplisitt framfor å arves.
nf <- function(x, desimaler = 1) {
  ut <- formatC(x, format = "f", digits = desimaler, big.mark = " ",
                decimal.mark = ",")
  trimws(ut)
}

skala_drivlinje <- function(...) {
  ggplot2::scale_colour_manual(values = FARGER, na.value = FARGER[["ovrig"]], ...)
}

tema_veitransport <- function(basisstorrelse = 11) {
  ggplot2::theme_minimal(base_size = basisstorrelse) +
    ggplot2::theme(
      panel.grid.minor = ggplot2::element_blank(),
      panel.grid.major.x = ggplot2::element_blank(),
      panel.border = ggplot2::element_blank(),
      axis.title = ggplot2::element_text(size = ggplot2::rel(0.9)),
      plot.title = ggplot2::element_text(face = "bold", size = ggplot2::rel(1.1)),
      plot.subtitle = ggplot2::element_text(colour = "#444444"),
      plot.caption = ggplot2::element_text(colour = "#666666", hjust = 0,
                                           size = ggplot2::rel(0.8)),
      plot.caption.position = "plot",
      plot.title.position = "plot",
      legend.position = "none"
    )
}

#' Kildelinje med tabellnummer, uttrekksdato og kodeversjon.
#'
#' Designdokumentet krever at hver figur bærer kilde og vintage. Linjen bygges fra
#' manifestet framfor å skrives inn for hånd, slik at den ikke kan bli stående og
#' vise til et uttrekk figuren ikke lenger hviler på.
kildelinje <- function(tabeller, prov, tillegg = NULL) {
  forste <- c(sprintf("Kilde: SSB %s", paste(tabeller, collapse = ", ")),
              sprintf("uttrekk %s", substr(prov$siste_uttrekk, 1, 10)))
  if (!is.null(tillegg)) forste <- append(forste, tillegg)
  andre <- sprintf("kode %s, commit %s, artefakter bygget %s", prov$kodeversjon,
                   prov$commit, substr(prov$bygget, 1, 10))
  # to linjer framfor én lang: en kildelinje som klippes av figurkanten, er
  # verre enn ingen, fordi den ser fullstendig ut
  paste(paste(forste, collapse = " · "), andre, sep = "\n")
}
