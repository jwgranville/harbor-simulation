#!/usr/bin/env python3
# tests/unit/test_terrain.py

import math
import pytest

from harbor_simulation.exceptions import AmbiguousTerrainElevationError
from harbor_simulation.quantitative import (
    Displacement,
    Distance,
    Point,
    Position,
)
from harbor_simulation.spatial import (
    GlobalPlacement,
    Orientation,
    RectangularExtent,
)
from harbor_simulation.terrain import TerrainSurface, TriangularSurfacePatch
from tests.support import terrain_vertex

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-22T04:15:01+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def test_terrain_surface_interpolates_elevation(
    sloping_terrain: TerrainSurface,
) -> None:
    elevation = sloping_terrain.elevation_at(Position.from_components(2, 3))
    assert elevation == Distance(-3)


def test_shared_vertices_make_adjacent_patches_continuous() -> None:
    first = terrain_vertex(0, 0, 0)
    second = terrain_vertex(10, 0, -10)
    lower_patch = TriangularSurfacePatch(
        (first, second, terrain_vertex(0, -10, -10))
    )
    upper_patch = TriangularSurfacePatch(
        (first, second, terrain_vertex(0, 10, 10))
    )
    terrain = TerrainSurface((lower_patch, upper_patch))

    assert terrain.elevation_at(Position.from_components(5, 0)) == Distance(-5)
    assert terrain.vertical_span_at(Position.from_components(5, 0)) is None


def test_disconnected_coincident_edges_form_vertical_face() -> None:
    lower_start = terrain_vertex(0, 0, -5)
    lower_end = terrain_vertex(10, 0, -7)
    upper_start = terrain_vertex(0, 0, 2)
    upper_end = terrain_vertex(10, 0, 3)
    lower_patch = TriangularSurfacePatch(
        (lower_start, lower_end, terrain_vertex(0, -10, -10))
    )
    upper_patch = TriangularSurfacePatch(
        (upper_start, upper_end, terrain_vertex(0, 10, 5))
    )
    terrain = TerrainSurface((lower_patch, upper_patch))
    midpoint = Position.from_components(5, 0)

    assert terrain.vertical_span_at(midpoint) == (Distance(-6), Distance(2.5))
    with pytest.raises(AmbiguousTerrainElevationError):
        terrain.elevation_at(midpoint)


def test_maximum_elevation_within_finds_interior_shoal(
    interior_shoal_terrain: TerrainSurface,
) -> None:
    extent = RectangularExtent.from_dimensions(2, 4)
    region = extent.region_at(
        GlobalPlacement(Position.from_components(0, 20), Orientation(0))
    )

    elevation = interior_shoal_terrain.maximum_elevation_within(region)
    assert elevation == Distance(-1)


def test_maximum_elevation_within_swept_region_finds_crossed_shoal(
    channel_shoal_terrain: TerrainSurface,
) -> None:
    extent = RectangularExtent.from_dimensions(2, 4)
    region = extent.region_at(
        GlobalPlacement(Position.from_components(0, 20), Orientation(0))
    )
    swept = region.swept_by(Displacement.from_components(8, 0))

    elevation = channel_shoal_terrain.maximum_elevation_within(swept)
    assert elevation == Distance(-1)


def test_maximum_elevation_within_uses_patch_boundary_intersections() -> None:
    patch = TriangularSurfacePatch(
        (
            terrain_vertex(0, 0, 0),
            terrain_vertex(10, 0, 10),
            terrain_vertex(5, 10, 5),
        )
    )
    terrain = TerrainSurface((patch,))
    extent = RectangularExtent(
        Point.from_components(-1, 4), Point.from_components(11, 6)
    )
    region = extent.region_at(
        GlobalPlacement(Position.from_components(0, 0), Orientation(0))
    )

    assert terrain.maximum_elevation_within(region) == Distance(8)


def test_maximum_elevation_within_handles_rotated_region() -> None:
    patch = TriangularSurfacePatch(
        (
            terrain_vertex(0, 0, 0),
            terrain_vertex(20, 0, 20),
            terrain_vertex(0, 20, 0),
        )
    )
    terrain = TerrainSurface((patch,))
    extent = RectangularExtent(
        Point.from_components(-1, -2), Point.from_components(1, 2)
    )
    region = extent.region_at(
        GlobalPlacement(
            Position.from_components(5, 5), Orientation(math.pi / 2)
        )
    )

    assert terrain.maximum_elevation_within(region) == Distance(7)
