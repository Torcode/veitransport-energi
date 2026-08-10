"""Energifaktorer med primærkilde.

Kilde (lest og verifisert 2026-08-10): Statistisk sentralbyrå, Notater 2018/45
«Energiregnskap og -balanse. Dokumentasjon av statistikkproduksjonen fra
statistikkår 1990 og fremover», vedlegg A, tabell A2 (tetthet) og tabell A3
(energiinnhold), sidene 51-52.
PDF: https://www.ssb.no/energi-og-industri/artikler-og-publikasjoner/_attachment/369610

Definisjoner fra kilden:
- Energiinnholdet er NETTO teoretisk energiinnhold (netto brennverdi, NCV),
  eksklusiv latent varme fra vanndamp.
- Verdiene er gjennomsnittsverdier; faktisk energiinnhold varierer.
- «Diesel, ekskl. bioandel» og «Bensin» er fossilproduktene; innblandet
  biodrivstoff har egne, lavere faktorer.

Konsekvens for bruk (D-0018): omregning av salgsvolum (som inkluderer iblandet
bio) til energi krever et eksplisitt anslag på bioandel; uten det skal fossile
faktorer bare brukes på fossilandelen, og resultater merkes deretter.
"""
from __future__ import annotations

SOURCE = (
    "SSB Notater 2018/45, vedlegg A, tabell A2 (tetthet) og A3 (energiinnhold, "
    "netto brennverdi/NCV, gjennomsnittsverdier), s. 51-52"
)
SOURCE_URL = "https://www.ssb.no/energi-og-industri/artikler-og-publikasjoner/_attachment/369610"

# Tabell A2: tetthet, kg per liter
DENSITY_KG_PER_L: dict[str, float] = {
    "bensin": 0.74,
    "autodiesel_fossil": 0.84,   # «Diesel, eksl bioandel»
    "biodiesel": 0.88,
    "bioetanol": 0.791,
    "parafiner": 0.81,
    "marine_gassoljer": 0.84,
}

# Tabell A3: energiinnhold, GJ per tonn (netto brennverdi)
NCV_GJ_PER_TONN: dict[str, float] = {
    "bensin": 43.9,
    "autodiesel_fossil": 43.1,   # «Diesel, eksl. Bioandel»
    "biodiesel": 36.8,
    "bioetanol": 26.8,
    "parafiner": 43.1,
    "marine_gassoljer": 43.1,
}

# Avledet: MJ per liter = (GJ/tonn) x (kg/liter), fordi GJ/tonn = MJ/kg.
MJ_PER_LITER: dict[str, float] = {
    p: NCV_GJ_PER_TONN[p] * DENSITY_KG_PER_L[p] for p in NCV_GJ_PER_TONN
}

MJ_PER_KWH = 3.6  # definisjon


def mill_liter_to_gwh(mill_liter: float, product: str) -> float:
    """Omregn volum (mill. liter) til GWh med kildens NCV-faktorer.

    Gjelder KUN produktet slik kilden avgrenser det (fossilprodukter ekskl.
    bioandel). For salgsvolum med iblandet bio må bioandelen behandles separat.
    """
    if product not in MJ_PER_LITER:
        raise KeyError(f"ukjent produkt '{product}'; kjente: {sorted(MJ_PER_LITER)}")
    mj = mill_liter * 1e6 * MJ_PER_LITER[product]
    kwh = mj / MJ_PER_KWH
    return kwh / 1e6
