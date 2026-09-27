#!/usr/bin/env python3
# tests/unit/test_quantitative.py

from harbor_simulation.quantitative import (
    Position,
    Scalar,
    TimeDelta,
    TimeSpan,
    planar_barycentric_weights,
    planar_convex_hull,
    planar_convex_polygon_intersection,
    planar_segment_parameter,
)

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-21T19:29:06+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def test_time_span_reports_start_times_for_duration() -> None:
    span = TimeSpan.from_values(4, 8)

    assert span.start_times_for(TimeDelta(2)) == TimeSpan.from_values(4, 6)
    assert span.start_times_for(TimeDelta(4)) == TimeSpan.from_values(4, 4)
    assert span.start_times_for(TimeDelta(5)) is None


def test_planar_segment_parameter_reports_position_on_segment() -> None:
    start = Position.from_components(0, 0)
    end = Position.from_components(10, 0)
    midpoint = Position.from_components(5, 0)
    outside = Position.from_components(5, 1)

    midpoint_parameter = planar_segment_parameter(midpoint, start, end)
    outside_parameter = planar_segment_parameter(outside, start, end)

    assert midpoint_parameter == Scalar(0.5)
    assert outside_parameter is None


def test_planar_barycentric_weights_report_position_within_triangle() -> None:
    triangle = (
        Position.from_components(0, 0),
        Position.from_components(10, 0),
        Position.from_components(0, 10),
    )
    position = Position.from_components(2, 3)

    weights = planar_barycentric_weights(position, triangle)

    assert weights == (Scalar(0.5), Scalar(0.2), Scalar(0.3))


def test_planar_convex_hull_contains_outer_positions() -> None:
    positions = (
        Position.from_components(0, 0),
        Position.from_components(2, 0),
        Position.from_components(2, 2),
        Position.from_components(0, 2),
        Position.from_components(1, 1),
    )

    hull = planar_convex_hull(positions)

    assert hull == (
        Position.from_components(0, 0),
        Position.from_components(2, 0),
        Position.from_components(2, 2),
        Position.from_components(0, 2),
    )


def test_planar_convex_polygon_intersection_reports_overlap() -> None:
    triangle = (
        Position.from_components(0, 0),
        Position.from_components(10, 0),
        Position.from_components(0, 10),
    )
    square = (
        Position.from_components(2, 2),
        Position.from_components(8, 2),
        Position.from_components(8, 8),
        Position.from_components(2, 8),
    )

    intersection = planar_convex_polygon_intersection(triangle, square)
    expected = frozenset(
        (
            Position.from_components(2, 2),
            Position.from_components(8, 2),
            Position.from_components(2, 8),
        )
    )

    assert frozenset(intersection) == expected
