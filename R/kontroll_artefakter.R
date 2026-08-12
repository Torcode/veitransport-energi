#!/usr/bin/env Rscript
# Uavhengig kontroll av leveransen, kjort fra et annet verktoysett enn det som
# bygde den. Filen er med vilje ren ASCII, slik at den kan parses i enhver locale
# og faktisk rekker aa kjore UTF-8-vakten i R/oppstart.R.
#
# Kontrollen svarer paa ett spoersmaal: kan noen andre bruke disse artefaktene
# uten prosjektets Python-kode? R regner manifestets sjekksummer paa nytt, leser
# hver tabell, og skriver ut hovedtall som Python-testene sammenligner mot sin
# egen lesing. Er svaret nei, er artefaktene mellomregninger og ikke et produkt.
#
# Bruk:  Rscript R/kontroll_artefakter.R [utfil.json]

her <- dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1]))
source(file.path(her, "oppstart.R"))
rot <- last_prosjekt(normalizePath(file.path(her, "..")))

argumenter <- commandArgs(trailingOnly = TRUE)
utfil <- if (length(argumenter) > 0) argumenter[1] else file.path(rot, "R", "kontrollresultat.json")

manifest <- verifiser_manifest(rot)
if (!all(manifest$stemmer)) {
  feil <- manifest$artefakt[!manifest$stemmer]
  stop(sprintf("sjekksum stemmer ikke for: %s", paste(feil, collapse = ", ")))
}

hist <- les_artefakt("historical_statistics.csv", rot)
reg <- les_artefakt("assumption_register.csv", rot)
kohort <- les_artefakt("validation_cohort_model.csv", rot)
stab <- les_artefakt("control_survival_parameter_stability.csv", rot)

andel_el <- function(var, aar) {
  d <- hist[hist$variabel == var & hist$gruppe == "personbiler" &
              substr(hist$periode, 1, 4) == aar, ]
  sum(d$verdi[d$drivlinje == "elektrisitet"]) / sum(d$verdi) * 100
}

resultat <- list(
  r_versjon = paste(R.version$major, R.version$minor, sep = "."),
  utf8_locale = isTRUE(l10n_info()[["UTF-8"]]),
  # Vakt mot stille tegnoedeleggelse i figurtekst. Proevestrengen er en litteral i
  # R/design.R, ikke en verdi fra et artefakt: readr merker artefakttekst som
  # UTF-8 uansett locale og ville ikke avsloert noe, mens kildeparsingen -- som er
  # det som faktisk sviktet under bygget her -- goer det.
  tegnkontroll_kilde = "R/design.R:TEGNPROVE",
  tegnkontroll_lengde = nchar(TEGNPROVE),
  tegnkontroll_tekst = TEGNPROVE,
  artefakter_kontrollert = nrow(manifest),
  alle_sjekksummer_stemmer = all(manifest$stemmer),
  rader_historisk = nrow(hist),
  rader_antakelsesregister = nrow(reg),
  elandel_bestand_2025 = andel_el("bestand_3112", "2025"),
  elandel_kjorelengde_2025 = andel_el("kjorelengde_total", "2025"),
  storste_avvik_kohortmodell_pct = max(abs(kohort$avvik_pct[!is.na(kohort$avvik_pct) &
                                             kohort$periode >= 2016])),
  weibull_skala_spenn = list(
    elektrisitet = range(stab$weibull_scale[stab$drivlinje == "elektrisitet"]),
    ikke_elektrisk = range(stab$weibull_scale[stab$drivlinje == "ikke_elektrisk"])
  )
)

dir.create(dirname(utfil), showWarnings = FALSE, recursive = TRUE)
writeLines(jsonlite::toJSON(resultat, auto_unbox = TRUE, digits = 12, pretty = TRUE), utfil)
cat(sprintf("OK  %d artefakter kontrollert med R %s; resultat skrevet til %s\n",
            nrow(manifest), resultat$r_versjon, utfil))
