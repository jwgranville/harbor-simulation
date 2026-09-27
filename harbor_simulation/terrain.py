#!/usr/bin/env python3
# harbor_simulation/terrain.py

import dataclasses
import itertools
import math

from harbor_simulation.exceptions import (
    AmbiguousTerrainElevationError,
    InvalidTerrainGeometryError,
    OutOfDomainError,
)
from harbor_simulation.quantitative import (
    Distance,
    Position,
    planar_barycentric_weights,
    planar_convex_polygon_intersection,
    planar_segment_parameter,
)
from harbor_simulation.spatial import ConvexPolygon, RectangularRegion

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-21T19:45:16+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


@dataclasses.dataclass(frozen=True, eq=False)
class TerrainVertex:
    position: Position
    elevation: Distance


@dataclasses.dataclass(frozen=True)
class TerrainEdge:
    start: TerrainVertex
    end: TerrainVertex

    def elevation_at(self, position: Position) -> Distance | None:
        try:
            parameter = planar_segment_parameter(
                position, self.start.position, self.end.position
            )
        except OutOfDomainError as error:
            raise InvalidTerrainGeometryError(
                "terrain edge endpoints must differ"
            ) from error
        if parameter is None:
            return None
        difference = self.end.elevation - self.start.elevation
        return self.start.elevation + difference * parameter

    def shares_vertices_with(self, other: "TerrainEdge") -> bool:
        same_direction = self.start is other.start and self.end is other.end
        reverse_direction = self.start is other.end and self.end is other.start
        return same_direction or reverse_direction

    def is_plan_coincident_with(self, other: "TerrainEdge") -> bool:
        same_direction = (
            self.start.position == other.start.position
            and self.end.position == other.end.position
        )
        reverse_direction = (
            self.start.position == other.end.position
            and self.end.position == other.start.position
        )
        return same_direction or reverse_direction


@dataclasses.dataclass(frozen=True)
class TriangularSurfacePatch:
    vertices: tuple[TerrainVertex, TerrainVertex, TerrainVertex]

    def edges(self) -> tuple[TerrainEdge, TerrainEdge, TerrainEdge]:
        first, second, third = self.vertices
        edges = (
            TerrainEdge(first, second),
            TerrainEdge(second, third),
            TerrainEdge(third, first),
        )
        return edges

    def elevation_at(self, position: Position) -> Distance | None:
        triangle = tuple(vertex.position for vertex in self.vertices)
        try:
            weights = planar_barycentric_weights(position, triangle)
        except OutOfDomainError as error:
            raise InvalidTerrainGeometryError(
                "terrain patch vertices are collinear"
            ) from error
        if weights is None:
            return None
        elevation = sum(
            vertex.elevation.value * weight.value
            for vertex, weight in zip(self.vertices, weights, strict=True)
        )
        return Distance(elevation)

    def maximum_elevation_within(
        self, region: RectangularRegion | ConvexPolygon
    ) -> Distance | None:
        triangle = tuple(vertex.position for vertex in self.vertices)
        positions = planar_convex_polygon_intersection(
            triangle, _region_vertices(region)
        )
        elevations = (
            elevation
            for position in positions
            if (elevation := self.elevation_at(position)) is not None
        )
        return max(elevations, default=None)


@dataclasses.dataclass(frozen=True)
class TerrainSurface:
    patches: tuple[TriangularSurfacePatch, ...]

    def elevation_at(self, position: Position) -> Distance | None:
        if self.vertical_span_at(position) is not None:
            raise AmbiguousTerrainElevationError(
                "terrain elevation is multivalued at a vertical face"
            )

        elevations = tuple(
            elevation
            for patch in self.patches
            if (elevation := patch.elevation_at(position)) is not None
        )
        if not elevations:
            return None

        elevation = elevations[0]
        if any(
            not math.isclose(other.value, elevation.value)
            for other in elevations[1:]
        ):
            raise InvalidTerrainGeometryError(
                "overlapping terrain patches disagree on elevation"
            )
        return elevation

    def maximum_elevation_within(
        self, region: RectangularRegion | ConvexPolygon
    ) -> Distance | None:
        elevations = (
            elevation
            for patch in self.patches
            if (elevation := patch.maximum_elevation_within(region))
            is not None
        )
        return max(elevations, default=None)

    def vertical_span_at(
        self, position: Position
    ) -> tuple[Distance, Distance] | None:
        edges = tuple(edge for patch in self.patches for edge in patch.edges())
        spans = []
        for first, second in itertools.combinations(edges, 2):
            if first.shares_vertices_with(second):
                continue
            if not first.is_plan_coincident_with(second):
                continue

            first_elevation = first.elevation_at(position)
            second_elevation = second.elevation_at(position)
            if first_elevation is None or second_elevation is None:
                continue
            if math.isclose(first_elevation.value, second_elevation.value):
                continue
            spans.append(
                (
                    min(first_elevation, second_elevation),
                    max(first_elevation, second_elevation),
                )
            )

        if not spans:
            return None
        span = spans[0]
        if any(other != span for other in spans[1:]):
            raise InvalidTerrainGeometryError(
                "multiple vertical faces disagree at this position"
            )
        return span


def _region_vertices(
    region: RectangularRegion | ConvexPolygon,
) -> tuple[Position, ...]:
    if isinstance(region, RectangularRegion):
        return region.corners()
    return region.vertices
