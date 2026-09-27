#!/usr/bin/env python3
# tests/unit/test_facility.py

from harbor_simulation.berth import Berth
from harbor_simulation.definitions import create_second_vessel
from harbor_simulation.facility import (
    DockingAuthorized,
    DockingRequestRejected,
    Facility,
)
from harbor_simulation.quantitative import Time, TimeDelta, TimeSpan
from harbor_simulation.vessel import Vessel

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-26T16:21:59+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def test_facility_approves_available_berth_for_requesting_vessel(
    berth: Berth, facility: Facility, vessel: Vessel
) -> None:
    event = facility.request_docking(vessel, berth)

    assert event == DockingAuthorized(vessel, berth)
    assert berth.authorized_vessel is vessel
    assert not berth.is_available()


def test_facility_rejects_request_for_unavailable_berth(
    berth: Berth, facility: Facility, vessel: Vessel, second_vessel: Vessel
) -> None:
    facility.request_docking(vessel, berth)

    event = facility.request_docking(second_vessel, berth)

    assert event == DockingRequestRejected(second_vessel, berth)
    assert berth.authorized_vessel is vessel


def test_rejected_vessel_waits_until_retry_is_authorized(
    berth: Berth, facility: Facility, vessel: Vessel
) -> None:
    waiting_vessel = create_second_vessel()
    initial_position = waiting_vessel.presence.position

    first_event = facility.request_docking(vessel, berth)
    second_event = facility.request_docking(waiting_vessel, berth)

    assert first_event == DockingAuthorized(vessel, berth)
    assert second_event == DockingRequestRejected(waiting_vessel, berth)

    waiting_vessel.advance_through(TimeSpan.from_values(0, 15))

    assert waiting_vessel.presence.position == initial_position
    assert waiting_vessel.motion is None

    berth.dock(vessel)
    berth.begin_service(Time(10), TimeDelta(5))
    berth.advance_through(TimeSpan.from_values(10, 15))
    berth.depart(vessel)

    retry_event = facility.request_docking(waiting_vessel, berth)

    assert retry_event == DockingAuthorized(waiting_vessel, berth)
    assert berth.authorized_vessel is waiting_vessel

    waiting_vessel.begin_itinerary(Time(15))

    assert waiting_vessel.next_transition_time() == Time(20)
