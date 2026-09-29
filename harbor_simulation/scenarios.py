#!/usr/bin/env python3
# harbor_simulation/scenarios.py

import dataclasses

from harbor_simulation.definitions import (
    CHANNEL_SHOAL_TERRAIN,
    START_TIME,
    TIDAL_WATER_LEVEL,
    create_berth,
    create_deep_vessel,
    create_facility,
    create_shallow_vessel,
)
from harbor_simulation.navigation import (
    ConservativeTransitClearanceModel,
    UnderKeelClearanceConstraint,
)
from harbor_simulation.projection import (
    ActorReference,
    DockingEventProjection,
    DockingEventProjector,
    HarborStateProjection,
    HarborStateProjector,
    TransitClearanceProjection,
    TransitClearanceProjector,
)
from harbor_simulation.quantitative import Distance, Time, TimeDelta, TimeSpan

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-29T18:05:15+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


@dataclasses.dataclass(frozen=True)
class ResourceConflictScenarioResult:
    docking_events: tuple[DockingEventProjection, ...]
    states: tuple[HarborStateProjection, ...]
    transit_clearances: tuple[TransitClearanceProjection, ...]


def run_resource_conflict_scenario() -> ResourceConflictScenarioResult:
    berth = create_berth()
    facility = create_facility(berth)
    shallow_vessel = create_shallow_vessel()
    deep_vessel = create_deep_vessel()

    facility_reference = ActorReference("facility")
    berth_reference = ActorReference("berth")
    shallow_reference = ActorReference("shallow-vessel")
    deep_reference = ActorReference("deep-vessel")
    references = {
        facility: facility_reference,
        berth: berth_reference,
        shallow_vessel: shallow_reference,
        deep_vessel: deep_reference,
    }
    actors = (facility, berth, shallow_vessel, deep_vessel)
    state_projector = HarborStateProjector(references)
    docking_projector = DockingEventProjector(references)
    clearance = ConservativeTransitClearanceModel(
        CHANNEL_SHOAL_TERRAIN,
        TIDAL_WATER_LEVEL,
        UnderKeelClearanceConstraint(Distance(0)),
    )
    clearance_projector = TransitClearanceProjector(references, clearance)

    shallow_event = facility.request_docking(shallow_vessel, berth)
    berth.dock(shallow_vessel)
    berth.begin_service(START_TIME, TimeDelta(7))
    deep_event = facility.request_docking(deep_vessel, berth)
    shallow_docking = docking_projector.project(START_TIME, shallow_event)
    deep_rejection = docking_projector.project(START_TIME, deep_event)
    initial_state = state_projector.project(START_TIME, actors)
    initial_clearance = clearance_projector.project(
        START_TIME, deep_vessel, TimeSpan.from_values(0, 14)
    )

    retry_time = Time(7)
    berth.advance_through(TimeSpan(START_TIME, retry_time))
    berth.depart(shallow_vessel)
    shallow_vessel.begin_itinerary(retry_time)
    retry_event = facility.request_docking(deep_vessel, berth)
    deep_authorization = docking_projector.project(retry_time, retry_event)
    retry_state = state_projector.project(retry_time, actors)
    retry_clearance = clearance_projector.project(
        retry_time, deep_vessel, TimeSpan.from_values(7, 20)
    )

    shallow_vessel.advance_through(TimeSpan.from_values(7, 9))
    deep_start_time = retry_clearance.start_spans[0].start
    deep_vessel.begin_itinerary(deep_start_time)
    transit_state = state_projector.project(deep_start_time, actors)

    deep_arrival_time = Time(18)
    deep_vessel.advance_through(TimeSpan(deep_start_time, deep_arrival_time))
    berth.dock(deep_vessel)
    final_state = state_projector.project(deep_arrival_time, actors)

    docking_events = (shallow_docking, deep_rejection, deep_authorization)
    states = (initial_state, retry_state, transit_state, final_state)
    transit_clearances = (initial_clearance, retry_clearance)
    result = ResourceConflictScenarioResult(
        docking_events, states, transit_clearances
    )
    return result
