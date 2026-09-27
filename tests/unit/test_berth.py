#!/usr/bin/env python3
# tests/unit/test_berth.py

import pytest

from harbor_simulation.berth import Berth
from harbor_simulation.exceptions import InvalidBerthOperationError
from harbor_simulation.quantitative import (
    Displacement,
    Point,
    Position,
    Time,
    TimeDelta,
    TimeSpan,
)
from harbor_simulation.spatial import (
    GlobalPlacement,
    LocalPlacement,
    Orientation,
    RectangularExtent,
)
from harbor_simulation.vessel import Vessel

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-22T04:10:24+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def test_berth_completes_service_at_transition_time(
    berth: Berth, vessel: Vessel
) -> None:
    assert berth.is_available()

    berth.approve_docking(vessel)
    berth.dock(vessel)
    berth.begin_service(Time(10), TimeDelta(5))

    assert not berth.is_available()
    assert berth.docked_vessel is vessel
    assert berth.next_transition_time() == Time(15)

    berth.advance_through(TimeSpan.from_values(10, 15))

    assert not berth.is_available()
    assert berth.docked_vessel is vessel
    assert berth.service is not None
    assert berth.service.complete
    assert berth.next_transition_time() is None


def test_berth_releases_departed_vessel_after_service(
    berth: Berth, vessel: Vessel
) -> None:
    berth.approve_docking(vessel)
    berth.dock(vessel)
    berth.begin_service(Time(10), TimeDelta(5))

    with pytest.raises(InvalidBerthOperationError):
        berth.depart(vessel)

    berth.advance_through(TimeSpan.from_values(10, 15))
    berth.depart(vessel)

    assert berth.is_available()
    assert berth.authorized_vessel is None
    assert berth.docked_vessel is None
    assert berth.service is None


def test_berth_requires_authorization_before_docking(
    berth: Berth, vessel: Vessel
) -> None:
    with pytest.raises(InvalidBerthOperationError):
        berth.dock(vessel)


def test_berth_working_region_is_relative_to_host() -> None:
    placement = LocalPlacement(
        Displacement.from_components(10, 5), Orientation(0)
    )
    working_extent = RectangularExtent(
        Point.from_components(-2, 0), Point.from_components(2, 6)
    )
    berth = Berth(placement, working_extent)
    host = GlobalPlacement(Position.from_components(100, 50), Orientation(0))

    region = berth.working_region_at(host)

    expected_placement = GlobalPlacement(
        Position.from_components(110, 55), Orientation(0)
    )
    assert region == working_extent.region_at(expected_placement)
