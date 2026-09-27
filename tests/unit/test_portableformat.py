#!/usr/bin/env python3
# tests/unit/test_portableformat.py

import pytest
import ropemother.client.procedure

from harbor_simulation.exceptions import InvalidMessagePayloadError
from harbor_simulation.portableformat import (
    AdvanceThroughProcedureAdapter,
    BeginBerthServiceProcedureAdapter,
    NextTransitionTimeAdapter,
)
from harbor_simulation.quantitative import Time, TimeDelta

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-26T23:08:42+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def test_advance_through_adapter_rejects_invalid_invocations() -> None:
    adapter = AdvanceThroughProcedureAdapter()
    missing_span = ropemother.client.procedure.ProcedureInvocation.from_call()
    invalid_span = ropemother.client.procedure.ProcedureInvocation.from_call(
        Time(0)
    )

    with pytest.raises(InvalidMessagePayloadError):
        adapter.encode(missing_span)

    with pytest.raises(InvalidMessagePayloadError):
        adapter.encode(invalid_span)


def test_begin_service_adapter_rejects_invalid_invocations() -> None:
    adapter = BeginBerthServiceProcedureAdapter()
    missing_duration = (
        ropemother.client.procedure.ProcedureInvocation.from_call(Time(0))
    )
    invalid_start = ropemother.client.procedure.ProcedureInvocation.from_call(
        TimeDelta(1), TimeDelta(1)
    )
    invalid_duration = (
        ropemother.client.procedure.ProcedureInvocation.from_call(
            Time(0), Time(1)
        )
    )

    with pytest.raises(InvalidMessagePayloadError):
        adapter.encode(missing_duration)

    with pytest.raises(InvalidMessagePayloadError):
        adapter.encode(invalid_start)

    with pytest.raises(InvalidMessagePayloadError):
        adapter.encode(invalid_duration)


def test_next_transition_time_adapter_rejects_invalid_value() -> None:
    adapter = NextTransitionTimeAdapter()

    with pytest.raises(InvalidMessagePayloadError):
        adapter.decode(True)
