#!/usr/bin/env python3
# tests/integration/test_projection_messagebus.py

import pytest
import ropemother

from harbor_simulation.messagebus import (
    publish_resource_conflict_scenario,
    MessageBusDockingEventPublisher,
    MessageBusHarborStatePublisher,
    MessageBusTransitClearancePublisher,
)
from harbor_simulation.portableformat import (
    DOCKING_EVENT_PROJECTION_FORMAT,
    HARBOR_STATE_PROJECTION_FORMAT,
    TRANSIT_CLEARANCE_PROJECTION_FORMAT,
)
from harbor_simulation.projection import ActorReference, DockingOutcome
from harbor_simulation.quantitative import Time, TimeSpan
from harbor_simulation.scenarios import run_resource_conflict_scenario

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-27T16:50:14+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


@pytest.mark.asyncio
async def test_resource_conflict_is_observable_over_message_bus() -> None:
    bus = ropemother.AsyncDirectMessageBus(
        extra_formats=(
            DOCKING_EVENT_PROJECTION_FORMAT,
            HARBOR_STATE_PROJECTION_FORMAT,
            TRANSIT_CLEARANCE_PROJECTION_FORMAT,
        ),
        capture_sink=ropemother.InMemoryCaptureSink(),
    )
    docking_emitter = bus.register_emitter(
        msg_topic="simulation.docking.events",
        msg_producer="facility",
        msg_type="docking-authorized",
        additional_msg_types=("docking-request-rejected",),
        payload_format=DOCKING_EVENT_PROJECTION_FORMAT,
    )
    state_emitter = bus.register_emitter(
        msg_topic="simulation.harbor.state",
        msg_producer="simulation",
        msg_type="harbor-state",
        payload_format=HARBOR_STATE_PROJECTION_FORMAT,
    )
    clearance_emitter = bus.register_emitter(
        msg_topic="simulation.transit.clearance",
        msg_producer="navigation",
        msg_type="transit-clearance",
        payload_format=TRANSIT_CLEARANCE_PROJECTION_FORMAT,
    )
    docking_receiver = bus.subscribe(msg_topic="simulation.docking.events")
    state_receiver = bus.subscribe(msg_topic="simulation.harbor.state")
    clearance_receiver = bus.subscribe(
        msg_topic="simulation.transit.clearance"
    )

    await publish_resource_conflict_scenario(
        docking_emitter, state_emitter, clearance_emitter
    )

    docking_messages = await docking_receiver.receive_batch(
        min_count=3, max_count=3
    )
    state_messages = await state_receiver.receive_batch(
        min_count=4, max_count=4
    )
    clearance_messages = await clearance_receiver.receive_batch(
        min_count=2, max_count=2
    )
    docking_events = tuple(message.payload for message in docking_messages)
    states = tuple(message.payload for message in state_messages)
    clearances = tuple(message.payload for message in clearance_messages)

    deep_vessel = ActorReference("deep-vessel")
    shallow_vessel = ActorReference("shallow-vessel")
    berth = ActorReference("berth")
    assert tuple(event.outcome for event in docking_events) == (
        DockingOutcome.AUTHORIZED,
        DockingOutcome.REJECTED,
        DockingOutcome.AUTHORIZED,
    )
    assert docking_events[0].vessel == shallow_vessel
    assert docking_events[1].vessel == deep_vessel
    assert docking_events[2].vessel == deep_vessel
    assert all(event.berth == berth for event in docking_events)
    assert tuple(state.time for state in states) == (
        Time(0),
        Time(7),
        Time(16),
        Time(18),
    )
    assert states[0].berths[0].docked_vessel == shallow_vessel
    assert states[1].berths[0].authorized_vessel == deep_vessel
    assert states[1].berths[0].docked_vessel is None
    assert states[-1].berths[0].docked_vessel == deep_vessel
    assert tuple(clearance.evaluated_at for clearance in clearances) == (
        Time(0),
        Time(7),
    )
    assert clearances[0].start_spans == (TimeSpan.from_values(4, 6),)
    assert clearances[1].start_spans == (TimeSpan.from_values(16, 18),)


@pytest.mark.asyncio
async def test_docking_events_round_trip_over_message_bus() -> None:
    bus = ropemother.AsyncDirectMessageBus(
        extra_formats=(DOCKING_EVENT_PROJECTION_FORMAT,),
        capture_sink=ropemother.InMemoryCaptureSink(),
    )
    emitter = bus.register_emitter(
        msg_topic="simulation.docking.events",
        msg_producer="facility",
        msg_type="docking-authorized",
        additional_msg_types=("docking-request-rejected",),
        payload_format=DOCKING_EVENT_PROJECTION_FORMAT,
    )
    receiver = bus.subscribe(msg_topic="simulation.docking.events")
    publisher = MessageBusDockingEventPublisher(emitter)
    result = run_resource_conflict_scenario()

    for event in result.docking_events:
        await publisher.publish(event)

    messages = await receiver.receive_batch(min_count=3, max_count=3)
    events = tuple(message.payload for message in messages)
    msg_types = tuple(message.msg_type for message in messages)
    assert events == result.docking_events
    assert msg_types == (
        "docking-authorized",
        "docking-request-rejected",
        "docking-authorized",
    )


@pytest.mark.asyncio
async def test_harbor_states_round_trip_over_message_bus() -> None:
    bus = ropemother.AsyncDirectMessageBus(
        extra_formats=(HARBOR_STATE_PROJECTION_FORMAT,),
        capture_sink=ropemother.InMemoryCaptureSink(),
    )
    emitter = bus.register_emitter(
        msg_topic="simulation.harbor.state",
        msg_producer="simulation",
        msg_type="harbor-state",
        payload_format=HARBOR_STATE_PROJECTION_FORMAT,
    )
    receiver = bus.subscribe(msg_topic="simulation.harbor.state")
    publisher = MessageBusHarborStatePublisher(emitter)
    result = run_resource_conflict_scenario()

    for state in result.states:
        await publisher.publish(state)

    messages = await receiver.receive_batch(min_count=4, max_count=4)
    states = tuple(message.payload for message in messages)
    assert states == result.states


@pytest.mark.asyncio
async def test_transit_clearances_round_trip_over_message_bus() -> None:
    bus = ropemother.AsyncDirectMessageBus(
        extra_formats=(TRANSIT_CLEARANCE_PROJECTION_FORMAT,),
        capture_sink=ropemother.InMemoryCaptureSink(),
    )
    emitter = bus.register_emitter(
        msg_topic="simulation.transit.clearance",
        msg_producer="navigation",
        msg_type="transit-clearance",
        payload_format=TRANSIT_CLEARANCE_PROJECTION_FORMAT,
    )
    receiver = bus.subscribe(msg_topic="simulation.transit.clearance")
    publisher = MessageBusTransitClearancePublisher(emitter)
    result = run_resource_conflict_scenario()

    for clearance in result.transit_clearances:
        await publisher.publish(clearance)

    messages = await receiver.receive_batch(min_count=2, max_count=2)
    clearances = tuple(message.payload for message in messages)
    assert clearances == result.transit_clearances
