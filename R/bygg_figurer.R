#!/usr/bin/env Rscript
# Bygger figurene i figurer/ fra publiserte artefakter. Ren ASCII, av samme grunn
# som kontroll_artefakter.R: filen maa kunne parses foer UTF-8-vakten har kjort.
#
# Bruk:  Rscript R/bygg_figurer.R

her <- dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1]))
source(file.path(her, "oppstart.R"))
rot <- last_prosjekt(normalizePath(file.path(her, "..")))

mappe <- file.path(rot, "figurer")
dir.create(mappe, showWarnings = FALSE)

hist <- les_artefakt("historical_statistics.csv", rot)
prov <- proveniens(rot)

figurer <- list(
  "salg_segmentert.png" = figur_salg_segmentert(hist, prov),
  "elandel_bestand_mot_kjorelengde.png" = figur_andel_bestand_mot_kjorelengde(hist, prov)
)

oppforinger <- list()
for (navn in names(figurer)) {
  ggplot2::ggsave(file.path(mappe, navn), figurer[[navn]], width = 7.5, height = 4.8,
                  dpi = 150, device = ragg::agg_png, bg = "white")
  oppforinger[[navn]] <- list(
    tittel = figurer[[navn]]$labels$title,
    kildelinje = figurer[[navn]]$labels$caption,
    bygget_fra_artefakt = "historical_statistics.csv"
  )
  cat(sprintf("OK  figurer/%s\n", navn))
}

# Provenienssporet skrives som tekst, ikke som en sammenligning av bildepunkter.
# En byte-for-byte-kontroll av PNG-ene ville roeket paa ulike font- og
# bibliotekversjoner uten at noe faglig var galt; det denne fanger, er det som
# faktisk betyr noe -- at en figur i repoet viser til et artefakt eller en
# kodeversjon den ikke lenger er bygget fra.
spor <- list(
  kodeversjon = prov$kodeversjon,
  artefakt_commit = prov$commit,
  artefakter_bygget = prov$bygget,
  manifest_sha256 = digest::digest(
    file = file.path(rot, "artifacts", "release_manifest.json"), algo = "sha256"),
  figurer = oppforinger
)
writeLines(jsonlite::toJSON(spor, auto_unbox = TRUE, pretty = TRUE),
           file.path(mappe, "figurspor.json"))
cat(sprintf("OK  figurer/figurspor.json\nBygget fra kode %s, commit %s, arbeidstre %s\n",
            prov$kodeversjon, prov$commit, prov$arbeidstre))
