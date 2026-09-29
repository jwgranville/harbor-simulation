#!/usr/bin/env python3
# tests/integration/test_transport_messagebus.py

import pytest
import ropemother
import ropemother.service

from harbor_simulation.messagebus import (
    DOCKING_AUTHORIZED_MESSAGE_TYPE,
    DOCKING_EVENTS_TOPIC,
    DOCKING_REQUEST_REJECTED_MESSAGE_TYPE,
    FACILITY_PRODUCER,
    HARBOR_STATE_MESSAGE_TYPE,
    HARBOR_STATE_TOPIC,
    NAVIGATION_PRODUCER,
    SIMULATION_LIFECYCLE_TOPIC,
    SIMULATION_PRODUCER,
    SIMULATION_RUN_COMPLETED_MESSAGE_TYPE,
    SIMULATION_TOPIC,
    TRANSIT_CLEARANCE_MESSAGE_TYPE,
    TRANSIT_CLEARANCE_TOPIC,
    publish_resource_conflict_scenario,
)
from harbor_simulation.portableformat import (
    DOCKING_EVENT_PROJECTION_FORMAT,
    HARBOR_PORTABLE_FORMATS,
    HARBOR_STATE_PROJECTION_FORMAT,
    SIMULATION_RUN_COMPLETED_PROJECTION_FORMAT,
    TRANSIT_CLEARANCE_PROJECTION_FORMAT,
)

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-29T18:04:34+00:00"
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
                msg_topic=DOCKING_EVENTS_TOPIC,
                msg_producer=FACILITY_PRODUCER,
                msg_type=DOCKING_AUTHORIZED_MESSAGE_TYPE,
                additional_msg_types=(DOCKING_REQUEST_REJECTED_MESSAGE_TYPE,),
                payload_format=DOCKING_EVENT_PROJECTION_FORMAT,
            )
            state_emitter = await producer.register_emitter(
                msg_topic=HARBOR_STATE_TOPIC,
                msg_producer=SIMULATION_PRODUCER,
                msg_type=HARBOR_STATE_MESSAGE_TYPE,
                payload_format=HARBOR_STATE_PROJECTION_FORMAT,
            )
            clearance_emitter = await producer.register_emitter(
                msg_topic=TRANSIT_CLEARANCE_TOPIC,
                msg_producer=NAVIGATION_PRODUCER,
                msg_type=TRANSIT_CLEARANCE_MESSAGE_TYPE,
                payload_format=TRANSIT_CLEARANCE_PROJECTION_FORMAT,
            )
            completion_emitter = await producer.register_emitter(
                msg_topic=SIMULATION_LIFECYCLE_TOPIC,
                msg_producer=SIMULATION_PRODUCER,
                msg_type=SIMULATION_RUN_COMPLETED_MESSAGE_TYPE,
                payload_format=SIMULATION_RUN_COMPLETED_PROJECTION_FORMAT,
            )
            receiver = await consumer.subscribe(
                msg_topic=ropemother.topic_tree(SIMULATION_TOPIC)
            )

            result = await publish_resource_conflict_scenario(
                docking_emitter,
                state_emitter,
                clearance_emitter,
                completion_emitter,
            )

            messages = []
            while True:
                message = await receiver.receive()
                if message.msg_type == SIMULATION_RUN_COMPLETED_MESSAGE_TYPE:
                    completion = message.payload
                    break
                messages.append(message)
            docking_events = tuple(
                message.payload
                for message in messages
                if message.msg_topic == DOCKING_EVENTS_TOPIC
            )
            states = tuple(
                message.payload
                for message in messages
                if message.msg_topic == HARBOR_STATE_TOPIC
            )
            clearances = tuple(
                message.payload
                for message in messages
                if message.msg_topic == TRANSIT_CLEARANCE_TOPIC
            )

            assert completion.time == result.states[-1].time
            assert docking_events == result.docking_events
            assert states == result.states
            assert clearances == result.transit_clearances
        finally:
            producer.close()
            consumer.close()
