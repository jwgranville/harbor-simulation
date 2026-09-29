#!/usr/bin/env python3
# harbor_simulation/messagebus.py

import asyncio
import collections.abc
import dataclasses

import ropemother.broker.asyncendpoints
import ropemother.client.asyncrequest

from harbor_simulation.actor import Actor
from harbor_simulation.berth import Berth
from harbor_simulation.exceptions import InvalidMessagePayloadError
from harbor_simulation.facility import Facility
from harbor_simulation.portableformat import (
    DOCKING_EVENT_PROJECTION_FORMAT,
    HARBOR_STATE_PROJECTION_FORMAT,
    SIMULATION_RUN_COMPLETED_PROJECTION_FORMAT,
    TRANSIT_CLEARANCE_PROJECTION_FORMAT,
)
from harbor_simulation.projection import (
    ActorReference,
    DockingEventProjection,
    DockingEventProjector,
    DockingOutcome,
    HarborStateProjection,
    SimulationRunCompletedProjection,
    TransitClearanceProjection,
)
from harbor_simulation.quantitative import Time, TimeSpan
from harbor_simulation.scenarios import (
    ResourceConflictScenarioResult,
    run_resource_conflict_scenario,
)
from harbor_simulation.temporal import ActorFacade
from harbor_simulation.time import Clock
from harbor_simulation.vessel import Vessel

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-29T17:51:07+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


SIMULATION_TOPIC = "simulation"
DOCKING_EVENTS_TOPIC = "simulation.docking.events"
HARBOR_STATE_TOPIC = "simulation.harbor.state"
TRANSIT_CLEARANCE_TOPIC = "simulation.transit.clearance"
SIMULATION_LIFECYCLE_TOPIC = "simulation.lifecycle"

FACILITY_PRODUCER = "facility"
SIMULATION_PRODUCER = "simulation"
NAVIGATION_PRODUCER = "navigation"

DOCKING_AUTHORIZED_MESSAGE_TYPE = "docking-authorized"
DOCKING_REQUEST_REJECTED_MESSAGE_TYPE = "docking-request-rejected"
HARBOR_STATE_MESSAGE_TYPE = "harbor-state"
TRANSIT_CLEARANCE_MESSAGE_TYPE = "transit-clearance"
SIMULATION_RUN_COMPLETED_MESSAGE_TYPE = "simulation-run-completed"


@dataclasses.dataclass
class MessageBusDockingEventPublisher:
    emitter: ropemother.broker.asyncendpoints.AsyncEmitter

    async def publish(self, value: DockingEventProjection) -> None:
        if value.outcome is DockingOutcome.AUTHORIZED:
            msg_type = DOCKING_AUTHORIZED_MESSAGE_TYPE
        else:
            msg_type = DOCKING_REQUEST_REJECTED_MESSAGE_TYPE

        await self.emitter.emit(
            value,
            msg_type=msg_type,
            payload_format=DOCKING_EVENT_PROJECTION_FORMAT,
        )


@dataclasses.dataclass
class MessageBusHarborStatePublisher:
    emitter: ropemother.broker.asyncendpoints.AsyncEmitter

    async def publish(self, value: HarborStateProjection) -> None:
        await self.emitter.emit(
            value, payload_format=HARBOR_STATE_PROJECTION_FORMAT
        )


@dataclasses.dataclass
class MessageBusTransitClearancePublisher:
    emitter: ropemother.broker.asyncendpoints.AsyncEmitter

    async def publish(self, value: TransitClearanceProjection) -> None:
        await self.emitter.emit(
            value, payload_format=TRANSIT_CLEARANCE_PROJECTION_FORMAT
        )


@dataclasses.dataclass
class MessageBusSimulationRunCompletedPublisher:
    emitter: ropemother.broker.asyncendpoints.AsyncEmitter

    async def publish(self, value: SimulationRunCompletedProjection) -> None:
        await self.emitter.emit(
            value, payload_format=SIMULATION_RUN_COMPLETED_PROJECTION_FORMAT
        )


@dataclasses.dataclass
class MessageBusDockingRequestHandler:
    facility: Facility
    actors_by_reference: collections.abc.Mapping[ActorReference, Actor]
    event_projector: DockingEventProjector
    clock: Clock
    event_publisher: MessageBusDockingEventPublisher

    async def request_docking(
        self, vessel_reference: ActorReference, berth_reference: ActorReference
    ) -> None:
        vessel = self.actors_by_reference.get(vessel_reference)
        berth = self.actors_by_reference.get(berth_reference)
        if not isinstance(vessel, Vessel):
            raise InvalidMessagePayloadError(
                "docking request vessel reference must resolve to a Vessel"
            )
        if not isinstance(berth, Berth):
            raise InvalidMessagePayloadError(
                "docking request berth reference must resolve to a Berth"
            )

        event = self.facility.request_docking(vessel, berth)
        projection = self.event_projector.project(self.clock.time, event)
        await self.event_publisher.publish(projection)


@dataclasses.dataclass
class MessageBusActorFacade(ActorFacade):
    advance_clients: tuple[
        ropemother.client.asyncrequest.AsyncProcedureClient, ...
    ]
    transition_clients: tuple[
        ropemother.client.asyncrequest.AsyncProcedureClient, ...
    ]

    async def advance_through(self, span: TimeSpan) -> None:
        async with asyncio.TaskGroup() as tasks:
            for client in self.advance_clients:
                tasks.create_task(client(span))

    async def next_transition_time(self) -> Time | None:
        async with asyncio.TaskGroup() as tasks:
            queries = tuple(
                tasks.create_task(client())
                for client in self.transition_clients
            )

        transition_times = tuple(query.result() for query in queries)
        known_times = tuple(
            time for time in transition_times if time is not None
        )

        if known_times:
            return min(known_times)
        return None


async def publish_resource_conflict_scenario(
    docking_event_emitter: ropemother.broker.asyncendpoints.AsyncEmitter,
    harbor_state_emitter: ropemother.broker.asyncendpoints.AsyncEmitter,
    transit_clearance_emitter: ropemother.broker.asyncendpoints.AsyncEmitter,
    completion_emitter: ropemother.broker.asyncendpoints.AsyncEmitter,
) -> ResourceConflictScenarioResult:
    result = run_resource_conflict_scenario()
    docking_publisher = MessageBusDockingEventPublisher(docking_event_emitter)
    state_publisher = MessageBusHarborStatePublisher(harbor_state_emitter)
    clearance_publisher = MessageBusTransitClearancePublisher(
        transit_clearance_emitter
    )
    completion_publisher = MessageBusSimulationRunCompletedPublisher(
        completion_emitter
    )

    for event in result.docking_events:
        await docking_publisher.publish(event)
    for state in result.states:
        await state_publisher.publish(state)
    for clearance in result.transit_clearances:
        await clearance_publisher.publish(clearance)

    completion = SimulationRunCompletedProjection(result.states[-1].time)
    await completion_publisher.publish(completion)
    return result
