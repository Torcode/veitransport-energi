"""Deklarative spesifikasjoner for prosjektets kjernetabeller.

Spesifikasjonene er identiske med designportens uttrekk (analysis/design_gate/),
slik at fase 0-resultatene forblir reproduserbare fra samme definisjoner.
Endringer her er designendringer og skal innom beslutningsloggen.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TableSpec:
    table_id: str
    name: str                       # filnavn-stamme for cache og uttrekk
    value_codes: dict[str, list[str]]
    freq: str                       # "M" eller "A"
    expected_units: dict[str, str]  # ContentsCode -> forventet enhetstekst i metadata
    key_dims: tuple[str, ...] = field(default=())  # dimensjoner som sammen med Tid er nøkkel
    description: str = ""
    # Energibalansen leverer tomme celler uten statuskode for produkt/år-kombinasjoner
    # som ikke finnes i posten (strukturell glisenhet). Bare tabeller med dokumentert
    # slik egenskap får lov til dette; alle andre krever statuskode på manglende verdier.
    allow_unexplained_missing: bool = False


SPECS: list[TableSpec] = [
    TableSpec(
        table_id="03687",
        name="sales_03687",
        value_codes={
            "Region": ["0"], "Kjopegrupper": ["00"],
            "PetroleumProd": ["00", "03", "04"],
            "ContentsCode": ["Petroleum"], "Tid": ["*"],
        },
        freq="M",
        expected_units={"Petroleum": "mill. liter"},
        key_dims=("PetroleumProd",),
        description="Salg av petroleumsprodukter 1995M01-2016M07 (avsluttet); Diesel er udelt",
    ),
    TableSpec(
        table_id="11174",
        name="sales_11174",
        value_codes={
            "Region": ["0"], "Kjopegrupper": ["00"],
            "PetroleumProd": ["00", "03", "04a", "04b"],
            "ContentsCode": ["Petroleum"], "Tid": ["*"],
        },
        freq="M",
        expected_units={"Petroleum": "mill. liter"},
        key_dims=("PetroleumProd",),
        description="Salg av petroleumsprodukter 2010M01-2022M01 (avsluttet); brudd 2020 for autodiesel",
    ),
    TableSpec(
        table_id="13585",
        name="sales_13585",
        value_codes={
            "Kjopegrupper": ["00"],
            "Produkter": ["00", "01", "02a", "02b"],
            "ContentsCode": ["Total", "Petroleum", "Biodrivstoff"], "Tid": ["*"],
        },
        freq="M",
        expected_units={
            "Total": "mill. liter", "Petroleum": "mill. liter", "Biodrivstoff": "mill. liter",
        },
        key_dims=("Produkter", "ContentsCode"),
        description="Salg petroleum og biodrivstoff 2021M01- (levende); 2021 prikket for Total/Biodrivstoff",
    ),
    TableSpec(
        table_id="09654",
        name="prices_09654",
        value_codes={"PetroleumProd": ["031", "035"], "ContentsCode": ["Priser"], "Tid": ["*"]},
        freq="M",
        expected_units={"Priser": "kr per liter"},
        key_dims=("PetroleumProd",),
        description="Utsalgspriser bensin 95 og avgiftspliktig diesel 1986M08-",
    ),
    TableSpec(
        table_id="14020",
        name="firstreg_14020",
        value_codes={
            "TypeRegistrering": ["N", "B"], "DrivstoffType": ["19", "20", "21", "6"],
            "ContentsCode": ["Personbiler", "VareCampBiler"], "Tid": ["*"],
        },
        freq="M",
        expected_units={"Personbiler": "kjøretøy", "VareCampBiler": "kjøretøy"},
        key_dims=("TypeRegistrering", "DrivstoffType", "ContentsCode"),
        description="Førstegangsregistrerte 1995M01-; fossil er ikke delt i bensin/diesel",
    ),
    TableSpec(
        table_id="12906",
        name="firstreg_12906",
        value_codes={
            "Region": ["0"],
            "TypeRegistrering": ["N", "B"],
            "DrivstoffType": ["1", "2", "5", "13", "14", "15", "16", "17", "3", "4", "6"],
            "ContentsCode": ["Personbil1", "Varebil4", "Bobiler", "Kombibil5", "Ambulanse2"],
            "Tid": ["*"],
        },
        freq="A",
        expected_units={
            "Personbil1": "kjøretøy", "Varebil4": "kjøretøy", "Bobiler": "kjøretøy",
            "Kombibil5": "kjøretøy", "Ambulanse2": "kjøretøy",
        },
        key_dims=("TypeRegistrering", "DrivstoffType", "ContentsCode"),
        description=(
            "Førstegangsregistrerte 2019- med FULL drivstoffdeling (bensin/diesel/el/hydrogen/"
            "ladbar og ikke-ladbar hybrid) og bobiler skilt fra varebiler. Løser to mangler ved "
            "14020: udelt fossil, og varebiler slått sammen med campingbiler (D-0020). "
            "EuroKlasser eliminert (summen)."
        ),
    ),
    TableSpec(
        table_id="07849",
        name="stock_07849",
        value_codes={
            "Region": ["0"], "DrivstoffType": ["1", "2", "3", "4", "5", "6"],
            "ContentsCode": ["Personbil1", "Varebil4"], "Tid": ["*"],
        },
        freq="A",
        expected_units={"Personbil1": "kjøretøy", "Varebil4": "kjøretøy"},
        key_dims=("DrivstoffType", "ContentsCode"),
        description="Bestand per 31.12, 2008-; KjoringensArt eliminert (totalen); hybrid i 'annet'",
    ),
    TableSpec(
        table_id="12577",
        name="km_12577",
        value_codes={
            # Alle kjøretøytyper hentes, både aggregatene (0, 00, 15, 16, 17) og
            # underkategoriene (20-33). Uten underkategoriene kan ikke
            # koblingskontrollen mot bestand og førstegangsregistreringer avgjøre
            # hva aggregatene faktisk inneholder (fase 2, D-0020).
            "Kjoretoytype": ["0", "00", "15", "16", "17", "20", "21", "22", "23", "24",
                             "25", "26", "27", "28", "29", "30", "31", "32", "33"],
            "DrivstoffType": ["0", "1", "2", "18", "14", "15", "16", "17", "3", "4", "13", "7"],
            "ContentsCode": ["Kjorelengde", "GjsnittKjorelengde"], "Tid": ["*"],
        },
        freq="A",
        expected_units={"Kjorelengde": "mill. km", "GjsnittKjorelengde": "km"},
        key_dims=("Kjoretoytype", "DrivstoffType", "ContentsCode"),
        description="Kjørelengder 2005- med full drivlinjedeling; hybrid i bensin/diesel t.o.m. 2015",
    ),
    TableSpec(
        table_id="11561",
        name="energybalance_11561_road",
        value_codes={
            "Energibalanse": ["EB120201"], "EnergiProdukt": ["*"],
            "ContentsCode": ["*"], "Tid": ["*"],
        },
        freq="A",
        expected_units={"EnergibalansenPJ": "PJ", "EnergibalansenGWh": "GWh"},
        key_dims=("EnergiProdukt", "ContentsCode"),
        description="Energibalansens post 12.2.1 Veitransport 1990-; el-fordelingsmetode uavklart",
        allow_unexplained_missing=True,
    ),
]

SPECS_BY_NAME = {s.name: s for s in SPECS}
