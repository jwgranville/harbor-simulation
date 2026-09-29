#!/usr/bin/env python3
# tests/integration/test_temporal_messagebus.py

import asyncio

import pytest
import ropemother

from harbor_simulation.actor import Actor
from harbor_simulation.berth import Berth
from harbor_simulation.facility import Facility
from harbor_simulation.messagebus import (
    DOCKING_AUTHORIZED_MESSAGE_TYPE,
    DOCKING_EVENTS_TOPIC,
    DOCKING_REQUEST_REJECTED_MESSAGE_TYPE,
    MessageBusActorFacade,
    MessageBusDockingEventPublisher,
    MessageBusDockingRequestHandler,
)
from harbor_simulation.plan import Itinerary, LinearLeg
from harbor_simulation.portableformat import (
    ADVANCE_THROUGH_PROCEDURE_FORMAT,
    BEGIN_BERTH_SERVICE_PROCEDURE_FORMAT,
    DOCKING_EVENT_PROJECTION_FORMAT,
    DOCKING_REQUEST_PROCEDURE_FORMAT,
    NEXT_TRANSITION_TIME_FORMAT,
)
from harbor_simulation.projection import (
    ActorReference,
    DockingEventProjection,
    DockingEventProjector,
    DockingOutcome,
)
from harbor_simulation.quantitative import (
    Displacement,
    Distance,
    Point,
    Position,
    Time,
    TimeDelta,
    TimeSpan,
)
from harbor_simulation.spatial import (
    LocalPlacement,
    Orientation,
    Presence,
    RectangularExtent,
    SpatialService,
)
from harbor_simulation.temporal import TemporalCoordinator
from harbor_simulation.time import Timeline
from harbor_simulation.vessel import Vessel

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-29T18:03:48+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


@pytest.mark.asyncio
async def test_temporal_coordinator_advances_vessel_over_message_bus(
    bus: ropemother.AsyncDirectMessageBus, empty_timeline: Timeline
) -> None:
    initial_position = Position.from_components(10, 20)
    start_time = Time(0)
    presence = _presence_at(initial_position)

    leg = LinearLeg.from_coordinates((40, 60), 8)
    itinerary = Itinerary.from_legs(leg)
    draft = Distance(1)

    vessel = Vessel.from_itinerary(presence, itinerary, draft)
    vessel.begin_itinerary(start_time)

    facade, services = _connect_actors(bus, ("vessel-a", vessel))

    empty_timeline.schedule.add(Time(4), "first")
    coordinator = TemporalCoordinator(empty_timeline, facade)

    service_tasks = _serve_requests(services, 4)

    first_span, first_due = await coordinator.advance_toward(Time(10))
    assert first_span == TimeSpan.from_values(0, 4)
    assert first_due == ("first",)
    assert vessel.presence.position == Position.from_components(25, 40)

    empty_timeline.schedule.add(Time(6), "second")

    second_span, second_due = await coordinator.advance_toward(Time(10))
    assert second_span == TimeSpan.from_values(4, 6)
    assert second_due == ("second",)
    assert vessel.presence.position == Position.from_components(32.5, 50)

    third_span, third_due = await coordinator.advance_toward(Time(10))
    assert third_span == TimeSpan.from_values(6, 8)
    assert third_due == ()
    assert vessel.presence.position == Position.from_components(40, 60)

    fourth_span, fourth_due = await coordinator.advance_toward(Time(10))
    assert fourth_span == TimeSpan.from_values(8, 10)
    assert fourth_due == ()
    assert vessel.presence.position == Position.from_components(40, 60)

    await asyncio.gather(*service_tasks)


@pytest.mark.asyncio
async def test_actor_facade_coordinates_multiple_vessels(
    bus: ropemother.AsyncDirectMessageBus, empty_timeline: Timeline
) -> None:
    first_position = Position.from_components(0, 0)
    second_position = Position.from_components(0, 10)
    start_time = Time(0)
    draft = Distance(1)

    first_presence = _presence_at(first_position)
    second_presence = _presence_at(second_position)

    leg_a = LinearLeg.from_coordinates((10, 0), 5)
    first_itinerary = Itinerary.from_legs(leg_a)
    first_vessel = Vessel.from_itinerary(
        first_presence, first_itinerary, draft
    )
    first_vessel.begin_itinerary(start_time)

    leg_b = LinearLeg.from_coordinates((0, 30), 8)
    second_itinerary = Itinerary.from_legs(leg_b)
    second_vessel = Vessel.from_itinerary(
        second_presence, second_itinerary, draft
    )
    second_vessel.begin_itinerary(start_time)

    facade, services = _connect_actors(
        bus, ("vessel-a", first_vessel), ("vessel-b", second_vessel)
    )
    coordinator = TemporalCoordinator(empty_timeline, facade)

    service_tasks = _serve_requests(services, 3)

    first_span, first_due = await coordinator.advance_toward(Time(10))
    assert first_span == TimeSpan.from_values(0, 5)
    assert first_due == ()
    assert first_vessel.presence.position == Position.from_components(10, 0)
    assert second_vessel.presence.position == Position.from_components(0, 22.5)

    second_span, second_due = await coordinator.advance_toward(Time(10))
    assert second_span == TimeSpan.from_values(5, 8)
    assert second_due == ()
    assert first_vessel.presence.position == Position.from_components(10, 0)
    assert second_vessel.presence.position == Position.from_components(0, 30)

    third_span, third_due = await coordinator.advance_toward(Time(10))
    assert third_span == TimeSpan.from_values(8, 10)
    assert third_due == ()
    assert first_vessel.presence.position == Position.from_components(10, 0)
    assert second_vessel.presence.position == Position.from_components(0, 30)

    await asyncio.gather(*service_tasks)


@pytest.mark.asyncio
async def test_vessel_enters_berth_working_region_before_service(
    bus: ropemother.AsyncDirectMessageBus, empty_timeline: Timeline
) -> None:
    start_time = Time(0)
    vessel_position = Position.from_components(0, 0)
    facility_position = Position.from_components(10, 0)

    berth_placement = LocalPlacement(
        Displacement.from_components(2, 2), Orientation(0)
    )
    berth_extent = RectangularExtent(
        Point.from_components(0, -2), Point.from_components(4, 2)
    )
    berth = Berth(berth_placement, berth_extent)
    facility = Facility(_presence_at(facility_position), (berth,))
    berth_region = berth.working_region_at(facility.presence.placement())

    vessel_extent = RectangularExtent(
        Point.from_components(-1, -2), Point.from_components(1, 2)
    )
    berth_origin = facility.presence.placement().place(berth.placement)
    destination = berth_origin.transform(Point.from_components(1, 0))
    leg = LinearLeg(destination, TimeDelta(5))
    itinerary = Itinerary.from_legs(leg)
    vessel_presence = Presence(vessel_position, Orientation(0), vessel_extent)
    draft = Distance(1)
    vessel = Vessel.from_itinerary(vessel_presence, itinerary, draft)
    vessel.begin_itinerary(start_time)

    spatial_service = SpatialService()
    spatial_service.register(facility, facility.presence)
    spatial_service.register(vessel, vessel.presence)

    facade, services = _connect_actors(
        bus, ("facility-a", facility), ("vessel-a", vessel), ("berth-a", berth)
    )

    coordinator = TemporalCoordinator(empty_timeline, facade)

    service_tasks = _serve_requests(services, 3)

    begin_service_client, begin_service_service = _connect_berth_service(
        bus, "berth-a", berth
    )

    docking_event_emitter = bus.register_emitter(
        msg_topic=DOCKING_EVENTS_TOPIC,
        msg_producer="facility-a",
        msg_type=DOCKING_AUTHORIZED_MESSAGE_TYPE,
        additional_msg_types=(DOCKING_REQUEST_REJECTED_MESSAGE_TYPE,),
        payload_format=DOCKING_EVENT_PROJECTION_FORMAT,
    )
    docking_event_receiver = bus.subscribe(
        msg_topic=DOCKING_EVENTS_TOPIC,
        msg_producer="facility-a",
    )
    vessel_reference = ActorReference("vessel-a")
    berth_reference = ActorReference("berth-a")
    actor_references = {vessel: vessel_reference, berth: berth_reference}
    actors_by_reference = {vessel_reference: vessel, berth_reference: berth}

    docking_event_publisher = MessageBusDockingEventPublisher(
        docking_event_emitter
    )
    docking_event_projector = DockingEventProjector(actor_references)
    docking_request_handler = MessageBusDockingRequestHandler(
        facility,
        actors_by_reference,
        docking_event_projector,
        empty_timeline.clock,
        docking_event_publisher,
    )
    docking_request_client, docking_request_service = _connect_docking_request(
        bus, docking_request_handler
    )

    assert vessel not in spatial_service.contained_within(berth_region)
    assert berth.is_available()

    docking_request_task = asyncio.create_task(
        docking_request_service.handle()
    )
    await docking_request_client(vessel_reference, berth_reference)
    await docking_request_task

    published_event = await docking_event_receiver.receive()

    assert published_event.msg_producer == "facility-a"
    assert published_event.msg_type == DOCKING_AUTHORIZED_MESSAGE_TYPE
    assert published_event.payload == DockingEventProjection(
        Time(0),
        DockingOutcome.AUTHORIZED,
        vessel_reference,
        berth_reference,
    )
    assert berth.authorized_vessel is vessel
    assert berth.docked_vessel is None
    assert not berth.is_available()
    assert berth.service is None

    first_span, first_due = await coordinator.advance_toward(Time(20))
    assert first_span == TimeSpan.from_values(0, 5)
    assert first_due == ()
    assert vessel.presence.position == destination
    assert vessel in spatial_service.contained_within(berth_region)
    assert berth.docked_vessel is None
    assert berth.service is None

    berth.dock(vessel)
    assert berth.docked_vessel is vessel

    begin_service_task = asyncio.create_task(begin_service_service.handle())
    await begin_service_client(first_span.end, TimeDelta(7))
    await begin_service_task
    assert not berth.is_available()

    second_span, second_due = await coordinator.advance_toward(Time(20))
    assert second_span == TimeSpan.from_values(5, 12)
    assert second_due == ()
    assert vessel.presence.position == destination
    assert berth.service is not None
    assert berth.service.complete

    third_span, third_due = await coordinator.advance_toward(Time(20))
    assert third_span == TimeSpan.from_values(12, 20)
    assert third_due == ()
    assert vessel.presence.position == destination
    assert not berth.is_available()

    await asyncio.gather(*service_tasks)


@pytest.fixture
def bus() -> ropemother.AsyncDirectMessageBus:
    formats = (
        ADVANCE_THROUGH_PROCEDURE_FORMAT,
        BEGIN_BERTH_SERVICE_PROCEDURE_FORMAT,
        NEXT_TRANSITION_TIME_FORMAT,
    )
    capture_sink = ropemother.InMemoryCaptureSink()
    message_bus = ropemother.AsyncDirectMessageBus(
        extra_formats=formats, capture_sink=capture_sink
    )
    return message_bus


def _presence_at(position: Position) -> Presence:
    extent = RectangularExtent.from_dimensions(2, 4)
    return Presence(position, Orientation(0), extent)


def _connect_actors(
    bus: ropemother.AsyncDirectMessageBus,
    *actors: tuple[str, Actor],
) -> tuple[
    MessageBusActorFacade,
    tuple[ropemother.client.asyncrequest.AsyncProcedureService, ...],
]:
    advance_clients = []
    transition_clients = []
    services = []

    for endpoint_name, actor in actors:
        request_topic = f"simulation.actors.{endpoint_name}.time.requests"

        advance_client = bus.create_procedure_client(
            request_topic=request_topic,
            reply_topic="simulation.time.replies",
            requester_producer="temporal-coordinator",
            responder_producer=endpoint_name,
            request_msg_type="advance-through",
            reply_msg_type="advance-through-complete",
            procedure_invocation_format=ADVANCE_THROUGH_PROCEDURE_FORMAT,
        )
        advance_service = bus.create_procedure_service(
            request_topic=request_topic,
            reply_topic="simulation.time.replies",
            requester_producer="temporal-coordinator",
            responder_producer=endpoint_name,
            request_msg_type="advance-through",
            reply_msg_type="advance-through-complete",
            handler=actor.advance_through,
        )
        transition_client = bus.create_procedure_client(
            request_topic=request_topic,
            reply_topic="simulation.time.replies",
            requester_producer="temporal-coordinator",
            responder_producer=endpoint_name,
            request_msg_type="next-transition-time",
            reply_msg_type="next-transition-time-result",
        )
        transition_service = bus.create_procedure_service(
            request_topic=request_topic,
            reply_topic="simulation.time.replies",
            requester_producer="temporal-coordinator",
            responder_producer=endpoint_name,
            request_msg_type="next-transition-time",
            reply_msg_type="next-transition-time-result",
            handler=actor.next_transition_time,
            reply_payload_format=NEXT_TRANSITION_TIME_FORMAT,
        )

        advance_clients.append(advance_client)
        transition_clients.append(transition_client)
        services.extend((advance_service, transition_service))

    facade = MessageBusActorFacade(
        advance_clients=tuple(advance_clients),
        transition_clients=tuple(transition_clients),
    )
    return facade, tuple(services)


def _connect_docking_request(
    bus: ropemother.AsyncDirectMessageBus,
    handler: MessageBusDockingRequestHandler,
) -> tuple[
    ropemother.client.asyncrequest.AsyncProcedureClient,
    ropemother.client.asyncrequest.AsyncProcedureService,
]:
    client = bus.create_procedure_client(
        request_topic="simulation.actors.facility-a.requests",
        reply_topic="simulation.docking.replies",
        requester_producer="vessel-a",
        responder_producer="facility-a",
        request_msg_type="request-docking",
        reply_msg_type="request-docking-complete",
        procedure_invocation_format=DOCKING_REQUEST_PROCEDURE_FORMAT,
    )
    service = bus.create_procedure_service(
        request_topic="simulation.actors.facility-a.requests",
        reply_topic="simulation.docking.replies",
        requester_producer="vessel-a",
        responder_producer="facility-a",
        request_msg_type="request-docking",
        reply_msg_type="request-docking-complete",
        handler=handler.request_docking,
    )
    return client, service


def _connect_berth_service(
    bus: ropemother.AsyncDirectMessageBus, endpoint_name: str, berth: Berth
) -> tuple[
    ropemother.client.asyncrequest.AsyncProcedureClient,
    ropemother.client.asyncrequest.AsyncProcedureService,
]:
    request_topic = f"simulation.actors.{endpoint_name}.requests"
    client = bus.create_procedure_client(
        request_topic=request_topic,
        reply_topic="simulation.operations.replies",
        requester_producer="operations-coordinator",
        responder_producer=endpoint_name,
        request_msg_type="begin-service",
        reply_msg_type="begin-service-complete",
        procedure_invocation_format=BEGIN_BERTH_SERVICE_PROCEDURE_FORMAT,
    )
    service = bus.create_procedure_service(
        request_topic=request_topic,
        reply_topic="simulation.operations.replies",
        requester_producer="operations-coordinator",
        responder_producer=endpoint_name,
        request_msg_type="begin-service",
        reply_msg_type="begin-service-complete",
        handler=berth.begin_service,
    )
    return client, service


def _serve_requests(
    services: tuple[ropemother.client.asyncrequest.AsyncProcedureService, ...],
    count: int,
) -> tuple[asyncio.Task[None], ...]:
    tasks = []
    for service in services:
        requests = _handle_requests(service, count)
        task = asyncio.create_task(requests)
        tasks.append(task)
    return tuple(tasks)


async def _handle_requests(
    service: ropemother.client.asyncrequest.AsyncProcedureService, count: int
) -> None:
    for _ in range(count):
        await service.handle()
