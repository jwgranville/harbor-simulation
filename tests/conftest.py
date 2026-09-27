#!/usr/bin/env python3
# tests/conftest.py

import pytest

from harbor_simulation.berth import Berth
from harbor_simulation.definitions import (
    CHANNEL_SHOAL_TERRAIN,
    INTERIOR_SHOAL_TERRAIN,
    SLOPING_TERRAIN,
    START_TIME,
    TIDAL_WATER_LEVEL,
    ZERO_WATER_LEVEL,
    create_berth,
    create_deep_vessel,
    create_facility,
    create_second_vessel,
    create_vessel,
)
from harbor_simulation.facility import Facility
from harbor_simulation.terrain import TerrainSurface
from harbor_simulation.time import Clock, Schedule, Timeline
from harbor_simulation.vessel import Vessel
from harbor_simulation.water import UniformHarmonicWaterLevel

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-26T16:02:51+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


@pytest.fixture
def empty_timeline() -> Timeline:
    return Timeline(Clock(START_TIME), Schedule())


@pytest.fixture
def sloping_terrain() -> TerrainSurface:
    return SLOPING_TERRAIN


@pytest.fixture
def interior_shoal_terrain() -> TerrainSurface:
    return INTERIOR_SHOAL_TERRAIN


@pytest.fixture
def channel_shoal_terrain() -> TerrainSurface:
    return CHANNEL_SHOAL_TERRAIN


@pytest.fixture
def berth() -> Berth:
    return create_berth()


@pytest.fixture
def facility(berth: Berth) -> Facility:
    return create_facility(berth)


@pytest.fixture
def zero_water_level() -> UniformHarmonicWaterLevel:
    return ZERO_WATER_LEVEL


@pytest.fixture
def tidal_water_level() -> UniformHarmonicWaterLevel:
    return TIDAL_WATER_LEVEL


@pytest.fixture
def vessel() -> Vessel:
    vessel = create_vessel()
    vessel.begin_itinerary(START_TIME)
    return vessel


@pytest.fixture
def second_vessel() -> Vessel:
    vessel = create_second_vessel()
    vessel.begin_itinerary(START_TIME)
    return vessel


@pytest.fixture
def deep_vessel() -> Vessel:
    vessel = create_deep_vessel()
    vessel.begin_itinerary(START_TIME)
    return vessel
