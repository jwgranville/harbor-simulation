#!/usr/bin/env python3
# tests/integration/test_transport_messagebus.py

import pytest
import ropemother
import ropemother.service

from harbor_simulation.messagebus import publish_resource_conflict_scenario
from harbor_simulation.portableformat import (
    DOCKING_EVENT_PROJECTION_FORMAT,
    HARBOR_PORTABLE_FORMATS,
    HARBOR_STATE_PROJECTION_FORMAT,
    TRANSIT_CLEARANCE_PROJECTION_FORMAT,
)

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-27T22:53:31+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


@pytest.mark.asyncio
async def test_resource_conflict_round_trips_over_transport() -> None:
    with ropemother.service.LocalMessageBusHost(
        extra_formats=HARBOR_PORTABLE_FORMATS,
        capture_sink=ropemother.InMemoryCaptureSink(),
    ) as host:
        descriptor = host.connection_descriptor()
        producer = await ropemother.connect_async_message_bus(
            descriptor, extra_formats=HARBOR_PORTABLE_FORMATS
        )
        consumer = await ropemother.connect_async_message_bus(
            descriptor, extra_formats=HARBOR_PORTABLE_FORMATS
        )
        try:
            docking_emitter = await producer.register_emitter(
                msg_topic="simulation.docking.events",
                msg_producer="facility",
                msg_type="docking-authorized",
                additional_msg_types=("docking-request-rejected",),
                payload_format=DOCKING_EVENT_PROJECTION_FORMAT,
            )
            state_emitter = await producer.register_emitter(
                msg_topic="simulation.harbor.state",
                msg_producer="simulation",
                msg_type="harbor-state",
                payload_format=HARBOR_STATE_PROJECTION_FORMAT,
            )
            clearance_emitter = await producer.register_emitter(
                msg_topic="simulation.transit.clearance",
                msg_producer="navigation",
                msg_type="transit-clearance",
                payload_format=TRANSIT_CLEARANCE_PROJECTION_FORMAT,
            )
            docking_receiver = await consumer.subscribe(
                msg_topic="simulation.docking.events"
            )
            state_receiver = await consumer.subscribe(
                msg_topic="simulation.harbor.state"
            )
            clearance_receiver = await consumer.subscribe(
                msg_topic="simulation.transit.clearance"
            )

            result = await publish_resource_conflict_scenario(
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
            docking_events = tuple(
                message.payload for message in docking_messages
            )
            states = tuple(message.payload for message in state_messages)
            clearances = tuple(
                message.payload for message in clearance_messages
            )

            assert docking_events == result.docking_events
            assert states == result.states
            assert clearances == result.transit_clearances
        finally:
            producer.close()
            consumer.close()
