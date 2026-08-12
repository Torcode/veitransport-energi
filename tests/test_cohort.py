"""Kohortmodellen: bedre enn baseline, tidsdelt validert, og ærlig om hva den ikke vet."""
from __future__ import annotations

import numpy as np
import pytest

from veitransport_energi.cohort import (
    MAX_AGE,
    SurvivalParams,
    backcast,
    load_flows,
    simulate,
)

# Parametre estimert på 2009–2015 (se D-0027). Låst her slik at testene ikke
# kjører rutenettsøket på nytt for hver kjøring.
FITTED = {
    "ikke_elektrisk": SurvivalParams(20.2, 2.4),
    "elektrisitet": SurvivalParams(11.8, 4.4),
}
TEST_YEARS = [str(a) for a in range(2016, 2026)]


@pytest.fixture(scope="module")
def flows():
    return load_flows("personbiler")


def test_overlevelsen_er_avtakende_og_i_intervallet():
    ages = np.arange(MAX_AGE + 1)
    for p in FITTED.values():
        s = p.conditional(ages)
        assert ((s >= 0) & (s <= 1)).all()
        assert s[1] > s[10] > s[20], "betinget overlevelse skal falle med alderen"


def test_modellen_treffer_observert_bestand_paa_ti_aar(flows):
    """Kjernetesten: parametre estimert på 2009–2015, målt mot 2016–2025."""
    for drivlinje, p in FITTED.items():
        sim = simulate(flows, p, drivlinje, "2008", "2025")
        d = sim[sim["periode"].isin(TEST_YEARS)].dropna(subset=["observert"])
        avvik = ((d["modellert"] - d["observert"]) / d["observert"] * 100).abs()
        assert avvik.max() < 3.0, f"{drivlinje}: største avvik {avvik.max():.2f} %"


def test_kohortmodellen_slaar_rate_modellen_klart(flows):
    """Begrunnelsen for kompleksiteten. Baseline bommet 6,8–7,3 % på samme horisont."""
    from veitransport_energi.stockflow import backcast as rate_backcast

    rate = rate_backcast("personbiler", "grov", [str(a) for a in range(2010, 2016)],
                         "2015", "2025")
    rate_verst = rate[rate["horisont_aar"] == 10]["avvik_pct"].abs().max()

    kohort_verst = 0.0
    for drivlinje, p in FITTED.items():
        sim = simulate(flows, p, drivlinje, "2008", "2025")
        d = sim[sim["periode"] == "2025"].dropna(subset=["observert"])
        kohort_verst = max(kohort_verst,
                           abs((d["modellert"].iloc[0] - d["observert"].iloc[0])
                               / d["observert"].iloc[0] * 100))
    assert kohort_verst < rate_verst / 3, (
        f"kohort {kohort_verst:.2f} % mot rate {rate_verst:.2f} % — forbedringen skal være klar"
    )


def test_estimering_med_overlappende_aar_avvises():
    with pytest.raises(ValueError, match="overlapper"):
        backcast("personbiler", "elektrisitet", "2008", ["2012", "2016"], ["2016", "2017"])
    with pytest.raises(ValueError, match="etter estimeringsårene"):
        backcast("personbiler", "elektrisitet", "2008", ["2018"], ["2016"])


def test_restbestanden_er_liten_og_doer_ut(flows):
    """Konstruksjonen som lukker manglende historikk skal ikke bære resultatet."""
    sim = simulate(flows, FITTED["ikke_elektrisk"], "ikke_elektrisk", "2008", "2025")
    siste = sim[sim["periode"] == "2025"].iloc[0]
    assert siste["restandel_pct"] < 5.0, "restbestanden skal være liten ved slutten"
    andeler = sim.dropna(subset=["restandel_pct"])["restandel_pct"].tolist()
    assert andeler[-1] < andeler[len(andeler) // 2], "restbestanden skal avta"


def test_elbilenes_kurvehale_er_ikke_belagt_med_data(flows):
    """Den viktigste begrensningen: modellen ekstrapolerer for høy alder.

    Elbilflåten er ung, så observasjonene identifiserer bare kurvens begynnelse.
    Testen låser at dette forblir synlig framfor å bli glemt.
    """
    p = FITTED["elektrisitet"]
    ages = np.arange(MAX_AGE + 1)
    s = p.conditional(ages)
    k = np.zeros(MAX_AGE + 1)
    nye, brukt = flows["nye"], flows["brukt"]
    for aar in [a for a in nye.index if int(a) <= 2025]:
        k[1:] = k[:-1] * s[:-1]
        k[0] = nye.loc[aar, "elektrisitet"]
        if aar in brukt.index:
            k[p.import_age] += brukt.loc[aar, "elektrisitet"]
    andel_over_8 = k[9:].sum() / k.sum()
    assert andel_over_8 < 0.15, (
        f"kun {andel_over_8:.1%} av elbilene er over 8 år — kurvens hale er ekstrapolasjon"
    )


def test_de_laste_parametrene_reproduseres_av_soket(flows):
    """Konstantene i FITTED_PARAMS skal komme fra estimeringen, ikke fra hånden."""
    from veitransport_energi.cohort import FITTED_PARAMS, fit_survival

    fit_aar = [str(a) for a in range(2009, 2016)]
    for drivlinje, ventet in FITTED_PARAMS.items():
        funnet, _ = fit_survival("personbiler", drivlinje, "2008", fit_aar, flows=flows)
        assert funnet.scale == ventet.scale, f"{drivlinje}: skala {funnet.scale} mot {ventet.scale}"
        assert funnet.shape == ventet.shape, f"{drivlinje}: form {funnet.shape} mot {ventet.shape}"


def test_formparameteren_flytter_seg_mer_enn_skalaen_over_vinduer():
    """Hva bestandsdata faktisk identifiserer — og hva de ikke gjør.

    Nivået på levetiden er pinnet av bestandsnivåene; hvor brått avgangen
    inntreffer, er det ikke. Skillet bærer usikkerhetsanalysen i fase 5, og
    testen låser at det ikke forsvinner stille.
    """
    from veitransport_energi.cohort import parameter_stability

    d = parameter_stability("personbiler", windows={
        "2009-2015": [str(a) for a in range(2009, 2016)],
        "2019-2025": [str(a) for a in range(2019, 2026)],
    })
    for drivlinje in ("elektrisitet", "ikke_elektrisk"):
        rad = d[d["drivlinje"] == drivlinje]
        skala_rel = (rad["weibull_scale"].max() / rad["weibull_scale"].min()) - 1
        form_rel = (rad["weibull_shape"].max() / rad["weibull_shape"].min()) - 1
        assert form_rel > skala_rel, (
            f"{drivlinje}: form {form_rel:.1%} skal flytte seg mer enn skala {skala_rel:.1%}"
        )
        assert skala_rel < 0.15, f"{drivlinje}: skalaen skal være rimelig stabil"


def test_framskrivingen_er_sterkt_folsom_for_overlevelsesparametrene(flows):
    """Følsomheten som må bæres videre til usikkerhetsanalysen i fase 5."""
    ages = np.arange(MAX_AGE + 1)
    nye, brukt = flows["nye"], flows["brukt"]

    def til_2035(p: SurvivalParams) -> float:
        s = p.conditional(ages)
        k = np.zeros(MAX_AGE + 1)
        for aar in [a for a in nye.index if int(a) <= 2025]:
            k[1:] = k[:-1] * s[:-1]
            k[0] = nye.loc[aar, "elektrisitet"]
            if aar in brukt.index:
                k[p.import_age] += brukt.loc[aar, "elektrisitet"]
        for _ in range(2026, 2036):
            k[1:] = k[:-1] * s[:-1]
            k[0] = 170000.0
        return float(k.sum())

    base = til_2035(FITTED["elektrisitet"])
    kort = til_2035(SurvivalParams(9.0, 4.4))
    lang = til_2035(SurvivalParams(18.0, 4.4))
    assert (base - kort) / base > 0.15, "kortere levetid skal gi vesentlig lavere bestand"
    assert (lang - base) / base > 0.20, "lengre levetid skal gi vesentlig høyere bestand"
