#!/usr/bin/env python3
# harbor_simulation/test_vessel.py

import pytest

from harbor_simulation.definitions import create_vessel
from harbor_simulation.exceptions import InvalidVesselOperationError
from harbor_simulation.quantitative import Position, Time, TimeSpan
from harbor_simulation.vessel import Vessel

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-26T16:19:43+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def test_vessel_reports_motion_end_as_next_transition_time(
    vessel: Vessel,
) -> None:
    assert vessel.next_transition_time() == Time(5)


def test_vessel_transitions_to_next_itinerary_leg_at_motion_end(
    vessel: Vessel,
) -> None:
    vessel.advance_through(TimeSpan.from_values(0, 5))
    current_leg = vessel.plan_state.current_leg()

    assert vessel.presence.position == Position.from_components(10, 0)
    assert vessel.plan_state.current_index == 1
    assert current_leg.destination == Position.from_components(10, 10)

    final_position = vessel.motion.position_at(Time(10))

    assert vessel.motion.span == TimeSpan.from_values(5, 10)
    assert vessel.next_transition_time() == Time(10)
    assert final_position == Position.from_components(10, 10)


def test_vessel_with_pending_itinerary_waits_until_itinerary_begins() -> None:
    vessel = create_vessel()
    initial_position = vessel.presence.position

    vessel.advance_through(TimeSpan.from_values(0, 4))

    assert vessel.presence.position == initial_position
    assert vessel.motion is None
    assert vessel.next_transition_time() is None

    vessel.begin_itinerary(Time(4))

    assert vessel.motion is not None
    assert vessel.motion.span == TimeSpan.from_values(4, 9)
    assert vessel.next_transition_time() == Time(9)


def test_vessel_cannot_begin_active_or_completed_itinerary(
    vessel: Vessel,
) -> None:
    with pytest.raises(InvalidVesselOperationError):
        vessel.begin_itinerary(Time(1))

    vessel.advance_through(TimeSpan.from_values(0, 5))
    vessel.advance_through(TimeSpan.from_values(5, 10))

    with pytest.raises(InvalidVesselOperationError):
        vessel.begin_itinerary(Time(10))
