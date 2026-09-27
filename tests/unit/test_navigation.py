#!/usr/bin/env python3
# tests/unit/test_navigation.py

import pytest

from harbor_simulation.definitions import create_deep_vessel
from harbor_simulation.exceptions import InvalidVesselOperationError
from harbor_simulation.navigation import (
    ConservativeTransitClearanceModel,
    UnderKeelClearanceConstraint,
)
from harbor_simulation.quantitative import Distance, Time, TimeSpan
from harbor_simulation.terrain import TerrainSurface
from harbor_simulation.vessel import Vessel
from harbor_simulation.water import (
    UniformHarmonicWaterLevel,
    UniformLevelWaterDepthModel,
)

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-26T16:20:54+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def test_whole_vessel_footprint_exposes_interior_shoal(
    interior_shoal_terrain: TerrainSurface,
    zero_water_level: UniformHarmonicWaterLevel,
    deep_vessel: Vessel,
) -> None:
    water_depth = UniformLevelWaterDepthModel(
        interior_shoal_terrain, zero_water_level
    )
    constraint = UnderKeelClearanceConstraint(Distance(0.25))

    reference_depth = water_depth.depth_at(
        deep_vessel.presence.position, Time(0)
    )
    assert reference_depth is not None
    assert constraint.is_satisfied_by(deep_vessel, reference_depth)

    region = deep_vessel.presence.region()
    for corner in region.corners():
        corner_depth = water_depth.depth_at(corner, Time(0))
        assert corner_depth is not None
        assert constraint.is_satisfied_by(deep_vessel, corner_depth)

    minimum_depth = water_depth.minimum_depth_within(region, Time(0))
    assert minimum_depth is not None
    assert not constraint.is_satisfied_by(deep_vessel, minimum_depth)


def test_harmonic_water_level_produces_clearance_windows(
    interior_shoal_terrain: TerrainSurface,
    tidal_water_level: UniformHarmonicWaterLevel,
    deep_vessel: Vessel,
) -> None:
    constraint = UnderKeelClearanceConstraint(Distance(0))
    region = deep_vessel.presence.region()
    terrain_elevation = interior_shoal_terrain.maximum_elevation_within(region)
    assert terrain_elevation is not None

    required_level = constraint.required_water_level(
        deep_vessel, terrain_elevation
    )
    spans = tidal_water_level.spans_at_or_above(
        required_level, TimeSpan.from_values(0, 18)
    )

    assert required_level == Distance(1)
    assert spans == (TimeSpan.from_values(4, 8), TimeSpan.from_values(16, 18))


def test_conservative_transit_clearance_gates_itinerary_start(
    channel_shoal_terrain: TerrainSurface,
    tidal_water_level: UniformHarmonicWaterLevel,
) -> None:
    vessel = create_deep_vessel()
    constraint = UnderKeelClearanceConstraint(Distance(0))
    clearance = ConservativeTransitClearanceModel(
        channel_shoal_terrain, tidal_water_level, constraint
    )

    start_spans = clearance.start_spans_for(
        vessel, TimeSpan.from_values(0, 14)
    )

    assert start_spans == (TimeSpan.from_values(4, 6),)
    assert not clearance.permits_start_at(vessel, Time(2))
    assert vessel.motion is None
    assert clearance.permits_start_at(vessel, Time(4))

    vessel.begin_itinerary(Time(4))

    assert vessel.motion is not None
    assert vessel.motion.span == TimeSpan.from_values(4, 6)


def test_conservative_transit_clearance_requires_pending_itinerary(
    channel_shoal_terrain: TerrainSurface,
    tidal_water_level: UniformHarmonicWaterLevel,
    deep_vessel: Vessel,
) -> None:
    constraint = UnderKeelClearanceConstraint(Distance(0))
    clearance = ConservativeTransitClearanceModel(
        channel_shoal_terrain, tidal_water_level, constraint
    )

    with pytest.raises(InvalidVesselOperationError):
        clearance.start_spans_for(deep_vessel, TimeSpan.from_values(0, 14))
