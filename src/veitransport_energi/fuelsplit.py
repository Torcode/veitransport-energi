"""Fordeling av drivstoffvolum på kjøretøygruppe, fra utslippsregnskapet.

Scenariodesignet (D-0032) navnga dette som problemet som avgjorde hva fase 5 kan
levere: kilometerne er kjent per kjøretøygruppe, men *volumet* er ikke. Den
kalibrerte energiintensiteten gjelder hele veitransporten under ett, og uten en
fordeling per gruppe kunne prosjektet bare framskrive kjøretøykilometer.

Denne modulen løser det, og løsningen krever ingen ny antatt størrelse.

## Hvorfor forholdstallene er volumandeler

CO2 per liter er en egenskap ved drivstoffet — karboninnholdet — ikke ved
kjøretøyet som brenner det. Et vogntog og en personbil slipper ut like mye CO2
per liter diesel. I utslippsregnskapet er utslippet derfor beregnet som volum
ganger en felles faktor per energivare, og forholdet mellom to kjøretøygruppers
CO2 fra samme energivare *er* forholdet mellom volumene deres.

Andelen kan altså leses ut uten å kjenne faktoren. Det er verdt å merke seg:
hadde vi gått veien om liter, måtte utslippsfaktoren vært hentet og verifisert,
og en feil i den ville slått rett inn i resultatet. Her forkortes den bort.

## Hva som følger av at regnskapet er fossilt

Utslippsregnskapet fører biogent CO2 fra innblandet biodrivstoff utenfor
totalen. Andelene her er derfor andeler av *fossilt* volum. Det passer
salgsstatistikken godt: petroleumsmåltallet i tabell 13585 er nettopp
fossildelen, og det er den serien prosjektet skjøter på (D-0002).

## Gruppene er kildens, ikke prosjektets

«Andre lette kjøretøy» i utslippsregnskapet er ikke identisk med prosjektets
varebilgruppe — den følger utslippsregnskapets egen avgrensning av lette
kjøretøy under 3,5 tonn. Sammenstillingen mellom de to inndelingene er derfor
omtrentlig og skal ikke brukes som om den var eksakt.
"""
from __future__ import annotations

import pandas as pd

from .datasets import read_extract

VEITRAFIKK_TOTALT = "5"
GRUPPER = {
    "personbiler": "5.1",
    "andre_lette": "5.2",
    "tunge": "5.3",
    "motorsykler": "5.4",
}
ENERGIVARE = {"bensin": "VT4", "diesel": "VT5"}
CO2 = "K11"


# Kildens statuskoder. Skillet er vesentlig: motorsykler har ingen dieselpost
# fordi kategorien ikke finnes, mens siste år mangler fordi regnskapet ennå ikke
# er publisert. Det første er en nullverdi, det andre er fravær av data, og å
# behandle dem likt ville enten kastet gyldige år eller talt uferdige år med.
STATUS_FINNES_IKKE = "."
STATUS_IKKE_TILGJENGELIG = (":", "..")


def _co2() -> pd.DataFrame:
    d = read_extract("emissions_13931_road")
    return d[d["UtslpKomp"] == CO2]


def _celle(serie_verdi: object, serie_status: object) -> tuple[float, bool]:
    """Verdi og om året kan brukes, gitt kildens statuskode."""
    status = (serie_status or "").strip() if isinstance(serie_status, str) else ""
    if status == STATUS_FINNES_IKKE:
        return 0.0, True
    if serie_verdi is None or pd.isna(serie_verdi):
        # Uferdig eller undertrykt: året kan ikke brukes til andeler.
        return float("nan"), False
    if status in STATUS_IKKE_TILGJENGELIG:
        # Skal ikke forekomme sammen med en verdi, men om kilden en dag leverer
        # begge deler, skal statusen veie tyngst framfor at tallet brukes stille.
        return float("nan"), False
    return float(serie_verdi), True


def volume_shares() -> pd.DataFrame:
    """Andel av fossilt drivstoffvolum per kjøretøygruppe, år for år.

    Én rad per år og energivare. `sum_kontroll_pct` er summen av gruppene målt
    mot kildens eget veitrafikktotal; avviker den fra 100, dekker ikke gruppene
    totalen, og andelene skal ikke brukes.
    """
    d = _co2()
    rows = []
    for baerer, vt in ENERGIVARE.items():
        f = d[d["UtslpEnergivare"] == vt]
        tot = f[f["UtslpTilLuft"] == VEITRAFIKK_TOTALT].set_index("Tid")
        per_gruppe = {navn: f[f["UtslpTilLuft"] == kode].set_index("Tid")
                      for navn, kode in GRUPPER.items()}
        for tid in sorted(tot.index):
            alle, ok = _celle(tot.loc[tid, "value"], tot.loc[tid, "status"])
            if not ok or not alle:
                continue
            deler, brukbar = {}, True
            for navn, tab in per_gruppe.items():
                if tid not in tab.index:
                    brukbar = False
                    break
                verdi, cell_ok = _celle(tab.loc[tid, "value"], tab.loc[tid, "status"])
                if not cell_ok:
                    brukbar = False
                    break
                deler[navn] = verdi
            if not brukbar:
                continue
            rad = {
                "kontroll": "volumandel_per_kjoretoygruppe",
                "energibaerer": baerer, "periode": tid,
                "co2_veitrafikk_1000t": alle,
                "sum_kontroll_pct": sum(deler.values()) / alle * 100,
                "status": "konstruert fra observerte data",
            }
            for navn, verdi in deler.items():
                rad[f"co2_{navn}_1000t"] = verdi
                rad[f"andel_{navn}_pct"] = verdi / alle * 100
            rows.append(rad)
    df = pd.DataFrame(rows)
    df["merknad"] = (
        "andel av fossilt drivstoffvolum, utledet av at CO2 per liter er en "
        "egenskap ved drivstoffet og ikke ved kjøretøyet; ingen utslippsfaktor "
        "er antatt. Biogent CO2 fra innblandet biodrivstoff føres utenfor "
        "regnskapet, så andelene gjelder petroleumsdelen av salget. "
        "«Andre lette kjøretøy» følger utslippsregnskapets avgrensning og er "
        "ikke identisk med prosjektets varebilgruppe"
    )
    return df


def volume_vs_distance() -> pd.DataFrame:
    """Volumandel mot kilometerandel — forskjellen scenariodesignet hviler på.

    Kilometerandelen sier hvor stor del av trafikkarbeidet en gruppe utfører;
    volumandelen sier hvor stor del av drivstoffet den bruker. For bensin er de
    nesten like. For diesel er de det ikke, fordi tunge kjøretøy bruker mange
    ganger mer per kilometer — og det er volumandelen som avgjør hva en
    framskriving av etterspørsel kan påstå.
    """
    from .coverage import estimand_coverage

    vol = volume_shares()
    km = estimand_coverage()
    km = km[km["energibaerer"].isin(ENERGIVARE)]

    sammen = km.merge(
        vol[["energibaerer", "periode", "andel_personbiler_pct", "andel_andre_lette_pct",
             "andel_tunge_pct", "andel_motorsykler_pct", "sum_kontroll_pct"]],
        on=["energibaerer", "periode"], how="inner", suffixes=("_km", "_volum"),
    )
    sammen["andel_innenfor_volum_pct"] = (sammen["andel_personbiler_pct_volum"]
                                          + sammen["andel_andre_lette_pct"])
    sammen["differanse_km_minus_volum_pp"] = (sammen["andel_innenfor_estimandet_pct"]
                                              - sammen["andel_innenfor_volum_pct"])
    sammen["kontroll"] = "kilometerandel_mot_volumandel"
    sammen["merknad"] = (
        "kilometerandelen er observert i kjørelengdestatistikken, volumandelen "
        "utledet av utslippsregnskapet. Positiv differanse betyr at gruppen kjører "
        "en større del av kilometerne enn den bruker av drivstoffet — altså at de "
        "som ligger utenfor, bruker mer per kilometer. Gruppene er ikke identisk "
        "avgrenset i de to kildene; sammenstillingen er omtrentlig"
    )
    kolonner = ["kontroll", "energibaerer", "periode",
                "andel_innenfor_estimandet_pct", "andel_innenfor_volum_pct",
                "differanse_km_minus_volum_pp", "andel_personbiler_pct_km",
                "andel_personbiler_pct_volum", "andel_tunge_pct", "sum_kontroll_pct",
                "merknad"]
    return sammen[kolonner].sort_values(["energibaerer", "periode"]).reset_index(drop=True)
