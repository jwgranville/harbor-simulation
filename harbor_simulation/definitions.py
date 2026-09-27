#!/usr/bin/env python3
# harbor_simulation/definitions.py

from harbor_simulation.berth import Berth
from harbor_simulation.facility import Facility
from harbor_simulation.plan import Itinerary, LinearLeg
from harbor_simulation.quantitative import (
    Displacement,
    Distance,
    Position,
    Time,
    TimeDelta,
)
from harbor_simulation.spatial import (
    LocalPlacement,
    Orientation,
    Presence,
    RectangularExtent,
)
from harbor_simulation.terrain import (
    TerrainSurface,
    TerrainVertex,
    TriangularSurfacePatch,
)
from harbor_simulation.vessel import Vessel
from harbor_simulation.water import UniformHarmonicWaterLevel

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-26T15:55:12+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"

CHART_DATUM_LEVEL = Distance(0)
FACING_EAST = Orientation(0)
STANDARD_VESSEL_EXTENT = RectangularExtent.from_dimensions(2, 4)
START_TIME = Time(0)
ZERO_OFFSET = Displacement.from_components(0, 0)

_BERTH_PLACEMENT = LocalPlacement(ZERO_OFFSET, FACING_EAST)

_FACILITY_POSITION = Position.from_components(8, 20)

_VESSEL_POSITION = Position.from_components(0, 0)
_VESSEL_FIRST_LEG = LinearLeg.from_coordinates((10, 0), 5)
_VESSEL_SECOND_LEG = LinearLeg.from_coordinates((10, 10), 5)
_VESSEL_ITINERARY = Itinerary.from_legs(_VESSEL_FIRST_LEG, _VESSEL_SECOND_LEG)
_VESSEL_DRAFT = Distance(1)

_SECOND_POSITION = Position.from_components(0, 10)
_SECOND_FIRST_LEG = LinearLeg.from_coordinates((10, 10), 5)
_SECOND_SECOND_LEG = LinearLeg.from_coordinates((10, 20), 5)
_SECOND_ITINERARY = Itinerary.from_legs(_SECOND_FIRST_LEG, _SECOND_SECOND_LEG)
_SECOND_DRAFT = Distance(1)

_SHALLOW_POSITION = Position.from_components(8, 20)
_SHALLOW_LEG = LinearLeg.from_coordinates((0, 20), 2)
_SHALLOW_ITINERARY = Itinerary.from_legs(_SHALLOW_LEG)
_SHALLOW_DRAFT = Distance(1)

_DEEP_POSITION = Position.from_components(0, 20)
_DEEP_LEG = LinearLeg.from_coordinates((8, 20), 2)
_DEEP_ITINERARY = Itinerary.from_legs(_DEEP_LEG)
_DEEP_DRAFT = Distance(2)


def create_berth() -> Berth:
    return Berth(_BERTH_PLACEMENT, STANDARD_VESSEL_EXTENT)


def create_facility(berth: Berth) -> Facility:
    presence = Presence(
        _FACILITY_POSITION, FACING_EAST, STANDARD_VESSEL_EXTENT
    )
    return Facility(presence, (berth,))


def create_vessel() -> Vessel:
    presence = Presence(_VESSEL_POSITION, FACING_EAST, STANDARD_VESSEL_EXTENT)
    return Vessel.from_itinerary(presence, _VESSEL_ITINERARY, _VESSEL_DRAFT)


def create_second_vessel() -> Vessel:
    presence = Presence(_SECOND_POSITION, FACING_EAST, STANDARD_VESSEL_EXTENT)
    return Vessel.from_itinerary(presence, _SECOND_ITINERARY, _SECOND_DRAFT)


def create_shallow_vessel() -> Vessel:
    presence = Presence(_SHALLOW_POSITION, FACING_EAST, STANDARD_VESSEL_EXTENT)
    return Vessel.from_itinerary(presence, _SHALLOW_ITINERARY, _SHALLOW_DRAFT)


def create_deep_vessel() -> Vessel:
    presence = Presence(_DEEP_POSITION, FACING_EAST, STANDARD_VESSEL_EXTENT)
    return Vessel.from_itinerary(presence, _DEEP_ITINERARY, _DEEP_DRAFT)


def _terrain_vertex(x: int, y: int, elevation: float) -> TerrainVertex:
    position = Position.from_components(x, y)
    return TerrainVertex(position, Distance(elevation))


def _sloping_terrain() -> TerrainSurface:
    southwest = _terrain_vertex(0, 0, 2)
    southeast = _terrain_vertex(10, 0, -8)
    northwest = _terrain_vertex(0, 10, -8)
    patch = TriangularSurfacePatch((southwest, southeast, northwest))
    return TerrainSurface((patch,))


def _interior_shoal_terrain(width: int, shoal_x: int) -> TerrainSurface:
    southwest = _terrain_vertex(0, 20, -5)
    southeast = _terrain_vertex(width, 20, -5)
    northeast = _terrain_vertex(width, 24, -5)
    northwest = _terrain_vertex(0, 24, -5)
    shoal = _terrain_vertex(shoal_x, 22, -1)
    south = TriangularSurfacePatch((southwest, southeast, shoal))
    east = TriangularSurfacePatch((southeast, northeast, shoal))
    north = TriangularSurfacePatch((northeast, northwest, shoal))
    west = TriangularSurfacePatch((northwest, southwest, shoal))
    return TerrainSurface((south, east, north, west))


def _zero_water_level() -> UniformHarmonicWaterLevel:
    mean_level = CHART_DATUM_LEVEL
    amplitude = Distance(0)
    period = TimeDelta(12)
    high_water_time = Time(0)
    water_level = UniformHarmonicWaterLevel(
        mean_level, amplitude, period, high_water_time
    )
    return water_level


def _tidal_water_level() -> UniformHarmonicWaterLevel:
    mean_level = CHART_DATUM_LEVEL
    amplitude = Distance(2)
    period = TimeDelta(12)
    high_water_time = Time(6)
    water_level = UniformHarmonicWaterLevel(
        mean_level, amplitude, period, high_water_time
    )
    return water_level


SLOPING_TERRAIN = _sloping_terrain()
INTERIOR_SHOAL_TERRAIN = _interior_shoal_terrain(2, 1)
CHANNEL_SHOAL_TERRAIN = _interior_shoal_terrain(10, 5)
ZERO_WATER_LEVEL = _zero_water_level()
TIDAL_WATER_LEVEL = _tidal_water_level()
