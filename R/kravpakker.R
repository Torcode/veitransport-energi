# Pakkene R-laget krever, deklarert ett sted. Ren ASCII, som resten av oppstarten.
#
# Listen finnes fordi CI feilet paa nettopp dette: knitr var installert i
# utviklingsmiljoeet, men manglet i workflow-filen, og feilen kom foerst til syne
# som et notat som ikke lot seg bygge -- langt fra aarsaken. Naa er kravet
# deklarert i koden, oppstarten stanser med navnet paa det som mangler, og en
# test krever at workflow-filen installerer hver eneste av dem.
#
# apt-navnet er "r-cran-" pluss pakkenavnet i sma bokstaver. Den regelen brukes
# baade av workflow-filen og av testen som sammenligner de to.

KREVDE_PAKKER <- c(
  "readr",     # innlesing av artefakter med eksplisitte typer
  "dplyr",     # filtrering og sammenstilling for framstilling
  "tidyr",     # pivotering i figurlaget
  "tibble",    # tabellform i manifestkontrollen
  "ggplot2",   # figurene
  "scales",    # akseformatering
  "ragg",      # PNG-enhet som handterer UTF-8 i figurtekst
  "jsonlite",  # manifest og kontrollresultat
  "digest",    # sha256 for uavhengig verifisering av manifestet
  "knitr"      # bygging av notatene i notat/
)

krev_pakker <- function(pakker = KREVDE_PAKKER) {
  mangler <- pakker[!vapply(pakker, requireNamespace, logical(1), quietly = TRUE)]
  if (length(mangler) == 0) return(invisible(TRUE))
  stop("R-laget mangler pakker: ", paste(mangler, collapse = ", "),
       ". Paa Debian/Ubuntu: sudo apt-get install -y ",
       paste0("r-cran-", tolower(mangler), collapse = " "),
       call. = FALSE)
}
