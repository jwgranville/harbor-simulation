#!/usr/bin/env python3
# tests/unit/test_water.py

import math
import pytest

from harbor_simulation.exceptions import OutOfDomainError
from harbor_simulation.quantitative import (
    Distance,
    Position,
    Time,
    TimeDelta,
    TimeSpan,
)
from harbor_simulation.spatial import (
    GlobalPlacement,
    Orientation,
    RectangularExtent,
)
from harbor_simulation.terrain import TerrainSurface, TriangularSurfacePatch
from harbor_simulation.water import (
    UniformHarmonicWaterLevel,
    UniformLevelWaterDepthModel,
    WaterDepthModel,
)
from tests.support import terrain_vertex

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-22T04:15:50+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def test_uniform_harmonic_water_level_rejects_invalid_parameters() -> None:
    with pytest.raises(OutOfDomainError):
        UniformHarmonicWaterLevel(
            mean_level=Distance(0),
            amplitude=Distance(-1),
            period=TimeDelta(12),
            high_water_time=Time(0),
        )

    with pytest.raises(OutOfDomainError):
        UniformHarmonicWaterLevel(
            mean_level=Distance(0),
            amplitude=Distance(1),
            period=TimeDelta(0),
            high_water_time=Time(0),
        )


def test_uniform_harmonic_water_level_repeats_cycle() -> None:
    water_level = UniformHarmonicWaterLevel(
        mean_level=Distance(2),
        amplitude=Distance(1),
        period=TimeDelta(12),
        high_water_time=Time(3),
    )
    position = Position.from_components(0, 0)

    assert water_level.water_level_at(position, Time(3)) == Distance(3)
    assert math.isclose(water_level.water_level_at(position, Time(6)).value, 2)
    assert water_level.water_level_at(position, Time(9)) == Distance(1)
    assert math.isclose(
        water_level.water_level_at(position, Time(12)).value, 2
    )
    assert water_level.water_level_at(position, Time(15)) == Distance(3)


def test_uniform_harmonic_water_level_finds_threshold_spans(
    tidal_water_level: UniformHarmonicWaterLevel,
) -> None:
    within = TimeSpan.from_values(0, 18)

    spans = tidal_water_level.spans_at_or_above(Distance(1), within)
    never = tidal_water_level.spans_at_or_above(Distance(3), within)
    always = tidal_water_level.spans_at_or_above(Distance(-3), within)
    expected = (TimeSpan.from_values(4, 8), TimeSpan.from_values(16, 18))

    assert spans == expected
    assert never == ()
    assert always == (within,)


def test_constant_uniform_water_level_finds_threshold_spans(
    zero_water_level: UniformHarmonicWaterLevel,
) -> None:
    within = TimeSpan.from_values(0, 18)

    assert zero_water_level.spans_at_or_above(Distance(0), within) == (within,)
    assert zero_water_level.spans_at_or_above(Distance(1), within) == ()


def test_uniform_harmonic_water_level_is_spatially_uniform() -> None:
    water_level = UniformHarmonicWaterLevel(
        mean_level=Distance(0),
        amplitude=Distance(1),
        period=TimeDelta(12),
        high_water_time=Time(0),
    )

    first = water_level.water_level_at(Position.from_components(0, 0), Time(2))
    second = water_level.water_level_at(
        Position.from_components(100, 50), Time(2)
    )

    assert first == second


def test_water_depth_combines_water_level_and_terrain_elevation(
    zero_water_level: UniformHarmonicWaterLevel,
) -> None:
    patch = TriangularSurfacePatch(
        (
            terrain_vertex(0, 0, -5),
            terrain_vertex(10, 0, 0),
            terrain_vertex(0, 10, -5),
        )
    )
    water_depth = WaterDepthModel(TerrainSurface((patch,)), zero_water_level)

    depth = water_depth.depth_at(Position.from_components(4, 2), Time(0))
    assert depth == Distance(3)


def test_uniform_water_depth_finds_minimum_depth_within_region(
    interior_shoal_terrain: TerrainSurface,
) -> None:
    level = UniformHarmonicWaterLevel(
        mean_level=Distance(2),
        amplitude=Distance(1),
        period=TimeDelta(12),
        high_water_time=Time(0),
    )
    water_depth = UniformLevelWaterDepthModel(interior_shoal_terrain, level)
    extent = RectangularExtent.from_dimensions(2, 4)
    region = extent.region_at(
        GlobalPlacement(Position.from_components(0, 20), Orientation(0))
    )

    assert water_depth.minimum_depth_within(region, Time(0)) == Distance(4)
    assert water_depth.minimum_depth_within(region, Time(6)) == Distance(2)
