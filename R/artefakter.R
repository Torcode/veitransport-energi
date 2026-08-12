# Innlesing av prosjektets artefakter i R.
#
# Dette laget beregner ingenting. Det leser de publiserte artefaktene og nekter å
# levere en tabell som ikke stemmer med manifestet. Poenget er ikke bekvemmelighet
# — Python-koden kan lese sine egne filer selv — men at et uavhengig verktøysett
# skal kunne bruke leveransen uten prosjektets egen kode. Klarer R å reprodusere
# manifestets sjekksummer og lese tabellene med riktige typer, er artefaktene et
# produkt andre kan bygge på. Klarer det ikke det, er de bare mellomregninger.
#
# Regelen som holder laget ærlig: ingen størrelse som ender i en figur eller en
# tekst, skal regnes ut her. Filtrering, sammenstilling og pivotering for
# framstilling er tillatt; estimering, kalibrering, skjøting, enhetsomregning og
# nye indikatorer hører hjemme i Python og skal komme hit ferdig som artefakt.

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(jsonlite)
  library(digest)
})

# Forutsetter at R/oppstart.R er kjørt først: den sikrer UTF-8 før parsing, og
# denne filen inneholder norske tegn som ellers ville blitt ødelagt stille.

rot_sti <- function() {
  sti <- Sys.getenv("VEITRANSPORT_ROT", unset = NA)
  if (is.na(sti)) stop("VEITRANSPORT_ROT er ikke satt — last laget med R/oppstart.R")
  normalizePath(sti, mustWork = TRUE)
}

artefaktmappe <- function(rot = rot_sti()) file.path(rot, "artifacts")

les_manifest <- function(rot = rot_sti()) {
  sti <- file.path(artefaktmappe(rot), "release_manifest.json")
  if (!file.exists(sti)) stop("release_manifest.json mangler — kjør artifacts-modulen i Python")
  jsonlite::fromJSON(sti, simplifyVector = FALSE)
}

#' Regn ut sjekksummene på nytt og sammenlign med manifestet.
#'
#' Uavhengig kontroll: R leser filene og regner sha256 selv, uten å spørre
#' Python-koden om noe. Er `stemmer` usann for en rad, er artefaktet endret etter
#' at manifestet ble skrevet, og ingenting bygget på det kan stoles på.
verifiser_manifest <- function(rot = rot_sti()) {
  m <- les_manifest(rot)
  navn <- names(m$artifacts)
  dplyr::bind_rows(lapply(navn, function(n) {
    sti <- file.path(artefaktmappe(rot), n)
    funnet <- if (file.exists(sti)) digest::digest(file = sti, algo = "sha256") else NA_character_
    tibble::tibble(
      artefakt = n,
      finnes = file.exists(sti),
      manifest_sha256 = m$artifacts[[n]]$sha256,
      lest_sha256 = funnet,
      rader_i_manifest = m$artifacts[[n]]$rows,
      stemmer = !is.na(funnet) && identical(funnet, m$artifacts[[n]]$sha256)
    )
  }))
}

#' Les ett artefakt, med manifestkontrollen som forutsetning.
#'
#' Feiler høyt framfor å levere noe som ser riktig ut. En figur bygget på et
#' artefakt som ikke stemmer med manifestet, ville vært verre enn ingen figur.
les_artefakt <- function(navn, rot = rot_sti()) {
  k <- verifiser_manifest(rot)
  rad <- k[k$artefakt == navn, ]
  if (nrow(rad) == 0) {
    stop(sprintf("'%s' står ikke i manifestet; kjente artefakter: %s",
                 navn, paste(k$artefakt, collapse = ", ")))
  }
  if (!rad$finnes) stop(sprintf("'%s' står i manifestet, men finnes ikke på disk", navn))
  if (!rad$stemmer) {
    stop(sprintf("'%s' avviker fra manifestets sjekksum — kjør artifacts-modulen på nytt", navn))
  }
  d <- readr::read_csv(file.path(artefaktmappe(rot), navn), show_col_types = FALSE,
                       progress = FALSE)
  if (nrow(d) != rad$rader_i_manifest) {
    stop(sprintf("'%s': %d rader lest, %d i manifestet", navn, nrow(d), rad$rader_i_manifest))
  }
  d
}

#' Datavintage og kodeversjon bak artefaktene, til kildelinjen i figurene.
proveniens <- function(rot = rot_sti()) {
  m <- les_manifest(rot)
  list(
    bygget = m$built_utc,
    commit = substr(m$git_commit, 1, 8),
    arbeidstre = m$arbeidstre,
    kodeversjon = m$code_version,
    tabeller = vapply(m$data_vintage, function(v) as.character(v$table_id), character(1)),
    siste_uttrekk = max(vapply(m$data_vintage, function(v) as.character(v$source_updated),
                               character(1)))
  )
}
