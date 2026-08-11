"""Avstemmingen mellom salgsstatistikk og energibalanse skal holde seg innenfor
et dokumentert bånd, og selve avstemmingsregelen skal kunne feile.
"""
from __future__ import annotations

import pytest

from veitransport_energi.diagnostics import energy_reconciliation

# Observert bånd 2010-2024 ved uttrekket 2026-08-11: 0,958-1,008 (median 0,983).
# Terskelen er satt romsligere enn observasjonen, men stramt nok til at en reell
# definisjons- eller faktorendring bryter den.
NEDRE, OVRE = 0.93, 1.05


@pytest.fixture(scope="module")
def rec(extracts):
    return energy_reconciliation(
        extracts["sales_11174"], extracts["sales_13585"], extracts["energybalance_11561_road"]
    )


def test_avstemming_dekker_hele_perioden(rec):
    assert rec.index.min() == 2010
    assert rec.index.max() >= 2024
    assert rec.index.is_monotonic_increasing
    assert rec["salgskilde"].loc[2024] == "13585"
    assert rec["salgskilde"].loc[2019] == "11174"


def test_energibalanse_og_salg_beskriver_samme_energimengde(rec):
    forhold = rec["eb_per_salg"]
    assert forhold.between(NEDRE, OVRE).all(), (
        "avstemmingen sprakk: " + forhold.round(3).to_string()
    )
    assert forhold.median() == pytest.approx(0.983, abs=0.02)


def test_avstemmingen_ville_sprukket_uten_biodrivstoffposten(rec):
    """Kontrollens skarphet: uten bioposten faller forholdstallet klart under båndet.

    Dette er begrunnelsen for at sammenligningen gjøres på SUMMEN og ikke per
    produkt: salgsvolumet inkluderer iblandet bio, energibalansens produktposter
    gjør det ikke.
    """
    uten_bio = rec["eb_fossil_PJ"] / rec["salgsenergi_PJ"]
    assert uten_bio.loc[2024] < NEDRE
    assert uten_bio.loc[2010] > NEDRE  # bio var ubetydelig i 2010


def test_kun_hele_ar_inngar(rec):
    """2022M01 finnes i begge salgstabellene; avstemmingen skal ikke dobbelttelle."""
    assert rec["salg_mill_liter_bensin"].loc[2022] < 1000
    assert 2026 not in rec.index  # inneværende år er ikke fullt
