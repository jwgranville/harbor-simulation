#!/usr/bin/env python3
# harbor_simulation/test_plan.py

from harbor_simulation.plan import LinearLeg, Itinerary, ItineraryState
from harbor_simulation.quantitative import (
    Displacement,
    Position,
    Time,
    TimeSpan,
)

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-15T19:05:54+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def test_linear_leg_manifests_motion_from_current_state() -> None:
    leg = LinearLeg.from_coordinates((20, 30), 5)

    motion = leg.manifest_from_coordinates((10, 10), 4)

    assert motion.span == TimeSpan.from_values(4, 9)
    assert motion.displacement() == Displacement.from_components(10, 20)
    assert motion.position_at(Time(4)) == Position.from_components(10, 10)
    assert motion.position_at(Time(9)) == Position.from_components(20, 30)


def test_itinerary_state_advances_between_legs() -> None:
    first = LinearLeg.from_coordinates((10, 0), 5)
    second = LinearLeg.from_coordinates((10, 10), 5)
    state = ItineraryState(Itinerary.from_legs(first, second))

    assert state.current_leg() == first

    state.advance()

    assert state.current_leg() == second
