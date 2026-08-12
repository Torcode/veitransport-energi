# Oppstart for R-laget. Denne filen er med vilje ren ASCII.
#
# Grunnen: R arver systemets locale, og i en tom locale (C) tolkes UTF-8-kildefiler
# feil allerede under parsing. Norske tegn blir da til punktum eller spoersmaalstegn
# stille, hele veien ut i figurtekst og tabelloverskrifter -- uten en eneste
# feilmelding. Feilen ble oppdaget her ved at en ferdig figur hadde "kj..relengde"
# i tittelen. En kontroll som bare sjekker at filen ble skrevet, ville godkjent den.
#
# Derfor: denne filen kan leses i enhver locale, den setter UTF-8 hvis den kan,
# og den stanser hoeyt hvis den ikke kan. Alt annet i R/ leses foerst etterpaa.
#
# Bruk:  source("R/oppstart.R"); last_prosjekt()

krev_utf8 <- function() {
  if (isTRUE(l10n_info()[["UTF-8"]])) return(invisible(TRUE))
  for (kandidat in c("C.UTF-8", "C.utf8", "en_US.UTF-8", "nb_NO.UTF-8", "Norwegian")) {
    suppressWarnings(try(Sys.setlocale("LC_ALL", kandidat), silent = TRUE))
    if (isTRUE(l10n_info()[["UTF-8"]])) return(invisible(TRUE))
  }
  stop("R kjorer uten UTF-8-locale. Norske tegn ville blitt oedelagt stille i ",
       "figurer og tabeller. Sett LANG=C.UTF-8 (Linux/macOS) eller bruk en ",
       "UTF-8-locale i Windows-sesjonen foer du kjorer noe herfra.",
       call. = FALSE)
}

prosjektrot <- function() {
  sti <- Sys.getenv("VEITRANSPORT_ROT", unset = NA)
  if (!is.na(sti)) return(normalizePath(sti, mustWork = TRUE))

  # Let oppover fra skriptets mappe, og deretter fra arbeidsmappen. Notatene
  # rendres fra notat/, skriptene kjores fra rot, og en RStudio-sesjon kan staa
  # hvor som helst -- roten skal finnes uansett.
  fil <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  start <- c(if (length(fil) > 0) dirname(sub("^--file=", "", fil[1])), getwd())
  for (s in start) {
    her <- normalizePath(s, mustWork = FALSE)
    for (i in 1:6) {
      if (file.exists(file.path(her, "pyproject.toml")) &&
            dir.exists(file.path(her, "artifacts"))) {
        return(normalizePath(her, mustWork = TRUE))
      }
      opp <- dirname(her)
      if (identical(opp, her)) break
      her <- opp
    }
  }
  stop("fant ikke prosjektroten; sett VEITRANSPORT_ROT eller kjor fra repoet",
       call. = FALSE)
}

#' Last R-laget med UTF-8 sikret foerst.
last_prosjekt <- function(rot = prosjektrot()) {
  krev_utf8()
  Sys.setenv(VEITRANSPORT_ROT = rot)
  for (f in c("artefakter.R", "design.R", "figurer.R")) {
    source(file.path(rot, "R", f), encoding = "UTF-8")
  }
  invisible(rot)
}
