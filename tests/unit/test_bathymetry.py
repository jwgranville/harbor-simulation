#!/usr/bin/env python3
# tests/unit/test_bathymetry.py

from harbor_simulation.bathymetry import Bathymetry
from harbor_simulation.quantitative import Distance, Position
from harbor_simulation.terrain import TerrainSurface

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-20T01:23:36+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def test_bathymetry_interprets_submerged_and_emerged_terrain(
    sloping_terrain: TerrainSurface,
) -> None:
    bathymetry = Bathymetry(sloping_terrain, Distance(0))

    submerged = Position.from_components(2, 3)
    emerged = Position.from_components(0, 0)
    outside = Position.from_components(10, 10)

    assert bathymetry.charted_depth_at(submerged) == Distance(3)
    assert bathymetry.charted_depth_at(emerged) == Distance(-2)
    assert bathymetry.charted_depth_at(outside) is None
