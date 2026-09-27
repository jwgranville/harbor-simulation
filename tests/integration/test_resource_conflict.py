#!/usr/bin/env python3
# tests/integration/test_resource_conflict.py

from harbor_simulation.definitions import START_TIME
from harbor_simulation.projection import (
    ActorReference,
    DockingEventProjection,
    DockingOutcome,
    TransitClearanceProjection,
)
from harbor_simulation.quantitative import Position, Time, TimeSpan
from harbor_simulation.scenarios import run_resource_conflict_scenario

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-26T17:41:46+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def test_berth_conflict_delays_deep_vessel_transit() -> None:
    result = run_resource_conflict_scenario()
    shallow_reference = ActorReference("shallow-vessel")
    deep_reference = ActorReference("deep-vessel")
    berth_reference = ActorReference("berth")

    expected_docking_events = (
        DockingEventProjection(
            START_TIME,
            DockingOutcome.AUTHORIZED,
            shallow_reference,
            berth_reference,
        ),
        DockingEventProjection(
            START_TIME,
            DockingOutcome.REJECTED,
            deep_reference,
            berth_reference,
        ),
        DockingEventProjection(
            Time(7),
            DockingOutcome.AUTHORIZED,
            deep_reference,
            berth_reference,
        ),
    )
    assert result.docking_events == expected_docking_events

    expected_clearances = (
        TransitClearanceProjection(
            START_TIME,
            deep_reference,
            TimeSpan.from_values(0, 14),
            (TimeSpan.from_values(4, 6),),
        ),
        TransitClearanceProjection(
            Time(7),
            deep_reference,
            TimeSpan.from_values(7, 20),
            (TimeSpan.from_values(16, 18),),
        ),
    )
    assert result.transit_clearances == expected_clearances

    initial_state, retry_state, transit_state, final_state = result.states
    assert tuple(state.time for state in result.states) == (
        START_TIME,
        Time(7),
        Time(16),
        Time(18),
    )

    initial_shallow, initial_deep = initial_state.vessels
    initial_berth = initial_state.berths[0]
    assert initial_shallow.motion_span is None
    assert initial_deep.motion_span is None
    assert initial_berth.authorized_vessel == shallow_reference
    assert initial_berth.docked_vessel == shallow_reference
    assert initial_berth.service is not None
    assert initial_berth.service.span == TimeSpan.from_values(0, 7)
    assert not initial_berth.service.complete

    retry_shallow, retry_deep = retry_state.vessels
    retry_berth = retry_state.berths[0]
    assert retry_shallow.motion_span == TimeSpan.from_values(7, 9)
    assert retry_deep.motion_span is None
    assert retry_berth.authorized_vessel == deep_reference
    assert retry_berth.docked_vessel is None
    assert retry_berth.service is None

    transit_shallow, transit_deep = transit_state.vessels
    assert transit_shallow.itinerary_complete
    assert transit_shallow.position == Position.from_components(0, 20)
    assert transit_deep.motion_span == TimeSpan.from_values(16, 18)

    final_shallow, final_deep = final_state.vessels
    final_berth = final_state.berths[0]
    assert final_shallow.itinerary_complete
    assert final_deep.itinerary_complete
    assert final_deep.motion_span is None
    assert final_deep.position == final_state.facilities[0].position
    assert final_berth.authorized_vessel == deep_reference
    assert final_berth.docked_vessel == deep_reference
