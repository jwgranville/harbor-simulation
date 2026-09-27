#!/usr/bin/env python3
# harbor_simulation/spatial.py

import abc
import dataclasses
import math
import numbers

from harbor_simulation.actor import Actor
from harbor_simulation.exceptions import UnsupportedSpatialOperationError
from harbor_simulation.quantitative import (
    Displacement,
    NumericValue,
    Point,
    Position,
    planar_convex_hull,
)

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-26T19:19:58+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


class SpatialService:
    def __init__(self) -> None:
        self._presences: dict[Actor, "Presence"] = {}

    def register(self, actor: Actor, presence: "Presence") -> None:
        self._presences[actor] = presence

    def intersecting(self, figure: "SpatialFigure") -> frozenset[Actor]:
        actors = frozenset(
            actor
            for actor, presence in self._presences.items()
            if figure.intersects(presence.region())
        )
        return actors

    def contained_within(self, region: "Region") -> frozenset[Actor]:
        actors = frozenset(
            actor
            for actor, presence in self._presences.items()
            if region.contains(presence.region())
        )
        return actors


@dataclasses.dataclass
class Presence:
    position: Position
    orientation: "Orientation"
    extent: "Extent"

    def placement(self) -> "GlobalPlacement":
        return GlobalPlacement(self.position, self.orientation)

    def region(self) -> "Region":
        return self.extent.region_at(self.placement())


@dataclasses.dataclass(frozen=True)
class Orientation(NumericValue):
    pass


@dataclasses.dataclass(frozen=True)
class LocalPlacement:
    offset: Displacement
    orientation: Orientation


@dataclasses.dataclass(frozen=True)
class GlobalPlacement:
    position: Position
    orientation: Orientation

    def place(self, local: LocalPlacement) -> "GlobalPlacement":
        offset = _rotate_displacement(local.offset, self.orientation)
        position = self.position + offset
        orientation = Orientation(
            self.orientation.value + local.orientation.value
        )
        return GlobalPlacement(position, orientation)

    def transform(self, point: Point) -> Position:
        offset = Displacement(point.coordinates)
        return self.position + _rotate_displacement(offset, self.orientation)


class SpatialFigure(abc.ABC):

    @abc.abstractmethod
    def intersects(self, other: "SpatialFigure") -> bool:
        pass


class Region(SpatialFigure):

    @abc.abstractmethod
    def contains(self, other: SpatialFigure) -> bool:
        pass


class Extent(abc.ABC):

    @abc.abstractmethod
    def region_at(self, placement: GlobalPlacement) -> Region:
        pass


@dataclasses.dataclass(frozen=True)
class ConvexPolygon:
    vertices: tuple[Position, ...]


@dataclasses.dataclass(frozen=True)
class RectangularRegion(Region):
    placement: GlobalPlacement
    extent: "RectangularExtent"

    def corners(self) -> tuple[Position, Position, Position, Position]:
        minimum_x, minimum_y = (
            coordinate.value for coordinate in self.extent.minimum.coordinates
        )
        maximum_x, maximum_y = (
            coordinate.value for coordinate in self.extent.maximum.coordinates
        )
        local_corners = (
            Point.from_components(minimum_x, minimum_y),
            Point.from_components(maximum_x, minimum_y),
            Point.from_components(maximum_x, maximum_y),
            Point.from_components(minimum_x, maximum_y),
        )
        corners = tuple(
            self.placement.transform(corner) for corner in local_corners
        )
        return corners

    def swept_by(self, displacement: Displacement) -> ConvexPolygon:
        start = self.corners()
        end = tuple(position + displacement for position in start)
        return ConvexPolygon(planar_convex_hull(start + end))

    def intersects(self, other: SpatialFigure) -> bool:
        if not isinstance(other, RectangularRegion):
            raise UnsupportedSpatialOperationError(
                "rectangle intersection requires a rectangular region"
            )

        left_minimum, left_maximum = _rectangular_bounds(self)
        right_minimum, right_maximum = _rectangular_bounds(other)
        pairs = zip(
            left_minimum,
            left_maximum,
            right_minimum,
            right_maximum,
            strict=True,
        )
        intersects = all(
            left_min <= right_max and right_min <= left_max
            for left_min, left_max, right_min, right_max in pairs
        )
        return intersects

    def contains(self, other: SpatialFigure) -> bool:
        if not isinstance(other, RectangularRegion):
            raise UnsupportedSpatialOperationError(
                "rectangle containment requires a rectangular region"
            )
        outer_minimum, outer_maximum = _rectangular_bounds(self)
        inner_minimum, inner_maximum = _rectangular_bounds(other)
        pairs = zip(
            outer_minimum,
            outer_maximum,
            inner_minimum,
            inner_maximum,
            strict=True,
        )
        contains = all(
            outer_min <= inner_min and inner_max <= outer_max
            for outer_min, outer_max, inner_min, inner_max in pairs
        )
        return contains


@dataclasses.dataclass(frozen=True)
class RectangularExtent(Extent):
    minimum: Point
    maximum: Point

    def region_at(self, placement: GlobalPlacement) -> RectangularRegion:
        return RectangularRegion(placement, self)

    @classmethod
    def from_dimensions(
        cls, x: numbers.Real, y: numbers.Real
    ) -> "RectangularExtent":
        return cls(Point.from_components(0, 0), Point.from_components(x, y))


def _rotate_displacement(
    displacement: Displacement, orientation: Orientation
) -> Displacement:
    if len(displacement.vector) != 2:
        raise UnsupportedSpatialOperationError(
            "rotation requires two dimensions"
        )

    x, y = (component.value for component in displacement.vector)
    cosine = math.cos(orientation.value)
    sine = math.sin(orientation.value)
    displacement = Displacement.from_components(
        x * cosine - y * sine, x * sine + y * cosine
    )
    return displacement


def _rectangular_bounds(
    region: RectangularRegion,
) -> tuple[tuple[numbers.Real, ...], tuple[numbers.Real, ...]]:
    if region.placement.orientation != Orientation(0):
        raise UnsupportedSpatialOperationError("rotated rectangular regions")

    minimum = region.placement.transform(region.extent.minimum)
    maximum = region.placement.transform(region.extent.maximum)
    minimum_values = tuple(value.value for value in minimum.point.coordinates)
    maximum_values = tuple(value.value for value in maximum.point.coordinates)
    return minimum_values, maximum_values
