#!/usr/bin/env python3
# tests/unit/test_spatial.py

import math

import pytest

from harbor_simulation.exceptions import UnsupportedSpatialOperationError
from harbor_simulation.facility import Facility
from harbor_simulation.quantitative import Displacement, Point, Position
from harbor_simulation.spatial import (
    GlobalPlacement,
    LocalPlacement,
    Orientation,
    Presence,
    RectangularExtent,
    RectangularRegion,
    SpatialService,
)

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-26T19:49:37+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def test_spatial_service_reports_geometric_relationships() -> None:
    inside = Facility(_presence_at(Position.from_components(1, 1)), ())
    partial = Facility(_presence_at(Position.from_components(4, 1)), ())
    outside = Facility(_presence_at(Position.from_components(7, 1)), ())

    spatial_service = SpatialService()
    spatial_service.register(inside, inside.presence)
    spatial_service.register(partial, partial.presence)
    spatial_service.register(outside, outside.presence)

    region = _region_at(Position.from_components(0, 0), 5, 5)

    assert spatial_service.intersecting(region) == frozenset((inside, partial))
    assert spatial_service.contained_within(region) == frozenset((inside,))


def test_spatial_service_uses_live_presence() -> None:
    actor = Facility(_presence_at(Position.from_components(10, 0)), ())

    spatial_service = SpatialService()
    spatial_service.register(actor, actor.presence)

    region = _region_at(Position.from_components(0, 0), 5, 5)
    assert spatial_service.intersecting(region) == frozenset()

    actor.presence.position = Position.from_components(2, 1)

    assert spatial_service.intersecting(region) == frozenset((actor,))
    assert spatial_service.contained_within(region) == frozenset((actor,))


def test_point_and_displacement_have_affine_algebra() -> None:
    point = Point.from_components(2, 3)
    displacement = Displacement.from_components(4, -1)

    assert point + displacement == Point.from_components(6, 2)
    assert point - displacement == Point.from_components(-2, 4)
    assert Point.from_components(6, 2) - point == displacement


def test_local_placement_resolves_from_global_origin() -> None:
    host = GlobalPlacement(Position.from_components(100, 50), Orientation(0))
    local = LocalPlacement(Displacement.from_components(10, 5), Orientation(0))

    placement = host.place(local)

    assert placement.position == Position.from_components(110, 55)
    assert placement.orientation == Orientation(0)


def test_local_placement_rotates_with_global_origin() -> None:
    host = GlobalPlacement(
        Position.from_components(100, 50), Orientation(math.pi / 2)
    )
    local = LocalPlacement(Displacement.from_components(10, 0), Orientation(0))

    placement = host.place(local)

    assert math.isclose(placement.position.point.coordinates[0].value, 100)
    assert math.isclose(placement.position.point.coordinates[1].value, 60)
    assert placement.orientation == Orientation(math.pi / 2)


def test_global_placement_rejects_nonplanar_offset() -> None:
    host = GlobalPlacement(Position.from_components(0, 0), Orientation(0))
    local = LocalPlacement(
        Displacement.from_components(1, 2, 3), Orientation(0)
    )

    with pytest.raises(UnsupportedSpatialOperationError):
        host.place(local)


def test_rectangular_extent_can_offset_from_local_origin() -> None:
    berth = GlobalPlacement(Position.from_components(110, 50), Orientation(0))
    extent = RectangularExtent(
        Point.from_components(-2, 0), Point.from_components(2, 6)
    )

    region = extent.region_at(berth)
    inside = RectangularExtent.from_dimensions(1, 1).region_at(
        GlobalPlacement(Position.from_components(109, 51), Orientation(0))
    )

    assert region.contains(inside)


def test_rectangular_region_reports_rotated_corners() -> None:
    extent = RectangularExtent(
        Point.from_components(-1, -2), Point.from_components(1, 2)
    )
    region = extent.region_at(
        GlobalPlacement(
            Position.from_components(10, 20), Orientation(math.pi / 2)
        )
    )

    corners = region.corners()

    expected = (
        Position.from_components(12, 19),
        Position.from_components(12, 21),
        Position.from_components(8, 21),
        Position.from_components(8, 19),
    )
    for actual, target in zip(corners, expected, strict=True):
        for actual_value, target_value in zip(
            actual.point.coordinates, target.point.coordinates, strict=True
        ):
            assert math.isclose(actual_value.value, target_value.value)


def test_rectangular_region_rejects_rotated_bounds() -> None:
    fixed = _region_at(Position.from_components(0, 0), 5, 5)
    rotated = RectangularExtent.from_dimensions(5, 5).region_at(
        GlobalPlacement(
            Position.from_components(0, 0), Orientation(math.pi / 4)
        )
    )

    with pytest.raises(UnsupportedSpatialOperationError):
        rotated.intersects(fixed)


def test_rectangular_region_reports_swept_polygon() -> None:
    extent = RectangularExtent(
        Point.from_components(0, 0), Point.from_components(2, 2)
    )
    region = extent.region_at(
        GlobalPlacement(Position.from_components(0, 0), Orientation(0))
    )

    swept = region.swept_by(Displacement.from_components(3, 2))

    assert swept.vertices == (
        Position.from_components(0, 0),
        Position.from_components(2, 0),
        Position.from_components(5, 2),
        Position.from_components(5, 4),
        Position.from_components(3, 4),
        Position.from_components(0, 2),
    )


def _presence_at(position: Position) -> Presence:
    extent = RectangularExtent.from_dimensions(2, 4)
    return Presence(position, Orientation(0), extent)


def _region_at(position: Position, x: int, y: int) -> RectangularRegion:
    extent = RectangularExtent.from_dimensions(x, y)
    return extent.region_at(GlobalPlacement(position, Orientation(0)))
