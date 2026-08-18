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
intens <- les_artefakt("reconstruction_intensity_bounds.csv", rot)
tilgang <- les_artefakt("inflow_by_drivetrain.csv", rot)
vol <- les_artefakt("control_volume_vs_distance.csv", rot)
prov <- proveniens(rot)

# Hver figur foeres med hvilket artefakt den hviler paa. Sporet under skriver det
# ut, slik at en figur som bytter grunnlag ikke kan gjoere det stille.
figurer <- list(
  "energibaner.png" = list(
    p = figur_energibaner(intens, prov), kilde = "reconstruction_intensity_bounds.csv"),
  "fossil_tilgang_mot_avgang.png" = list(
    p = figur_fossil_tilgang_mot_avgang(tilgang, prov), kilde = "inflow_by_drivetrain.csv"),
  "km_mot_volum.png" = list(
    p = figur_km_mot_volum(vol, prov), kilde = "control_volume_vs_distance.csv"),
  "elandel_bestand_mot_kjorelengde.png" = list(
    p = figur_andel_bestand_mot_kjorelengde(hist, prov), kilde = "historical_statistics.csv"),
  "salg_segmentert.png" = list(
    p = figur_salg_segmentert(hist, prov), kilde = "historical_statistics.csv")
)

oppforinger <- list()
for (navn in names(figurer)) {
  ggplot2::ggsave(file.path(mappe, navn), figurer[[navn]]$p, width = 7.5, height = 4.8,
                  dpi = 150, device = ragg::agg_png, bg = "white")
  oppforinger[[navn]] <- list(
    tittel = figurer[[navn]]$p$labels$title,
    bygget_fra_artefakt = figurer[[navn]]$kilde
  )
  cat(sprintf("OK  figurer/%s\n", navn))
}

# Provenienssporet skrives som tekst, ikke som en sammenligning av bildepunkter.
# En byte-for-byte-kontroll av PNG-ene ville roeket paa ulike font- og
# bibliotekversjoner uten at noe faglig var galt; det denne fanger, er det som
# faktisk betyr noe -- at en figur i repoet viser til et annet grunnlag enn det
# som ligger her.
#
# Sporet inneholder med vilje ingen stoerrelse som endrer seg av seg selv.
# Foerste utgave foerte ogsaa commit og byggetidspunkt fra manifestet, og da ble
# kontrollen roed hver gang artefaktene ble bygget paa nytt ved en ny HEAD --
# uten at figurene var feil. Manifestets sjekksum daekker begge deler: endrer
# artefaktene seg, endrer den seg.
spor <- list(
  kodeversjon = prov$kodeversjon,
  manifest_sha256 = digest::digest(
    file = file.path(rot, "artifacts", "release_manifest.json"), algo = "sha256"),
  figurer = oppforinger
)
writeLines(jsonlite::toJSON(spor, auto_unbox = TRUE, pretty = TRUE),
           file.path(mappe, "figurspor.json"))
cat(sprintf("OK  figurer/figurspor.json\nBygget fra kode %s, commit %s, arbeidstre %s\n",
            prov$kodeversjon, prov$commit, prov$arbeidstre))
