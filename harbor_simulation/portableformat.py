#!/usr/bin/env python3
# harbor_simulation/portableformat.py

import ropemother.client.procedure
import ropemother.format.portableformat
import ropemother.util.onelinejson
import ropemother.util.serializer

from harbor_simulation.exceptions import InvalidMessagePayloadError
from harbor_simulation.projection import (
    ActorReference,
    BerthServiceProjection,
    BerthStateProjection,
    DockingEventProjection,
    DockingOutcome,
    FacilityStateProjection,
    HarborStateProjection,
    TransitClearanceProjection,
    VesselStateProjection,
)
from harbor_simulation.quantitative import (
    Distance,
    Position,
    Time,
    TimeDelta,
    TimeSpan,
)
from harbor_simulation.spatial import Orientation

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-27T16:28:19+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


class DockingEventProjectionAdapter(
    ropemother.util.serializer.TypeAdapter[
        DockingEventProjection,
        ropemother.util.onelinejson.JSONRecord,
    ]
):

    def encode(
        self, value: DockingEventProjection
    ) -> ropemother.util.onelinejson.JSONRecord:
        data = {
            "time": value.time.value,
            "outcome": value.outcome.value,
            "vessel": value.vessel.value,
            "berth": value.berth.value,
        }
        return data

    def decode(
        self, data: ropemother.util.onelinejson.JSONRecord
    ) -> DockingEventProjection:
        time = _time_from_data(data.get("time"), "docking event time")
        outcome_data = data.get("outcome")
        if outcome_data == DockingOutcome.AUTHORIZED.value:
            outcome = DockingOutcome.AUTHORIZED
        elif outcome_data == DockingOutcome.REJECTED.value:
            outcome = DockingOutcome.REJECTED
        else:
            raise InvalidMessagePayloadError(
                "docking event outcome must be authorized or rejected"
            )
        vessel = _actor_reference_from_data(
            data.get("vessel"), "docking event vessel"
        )
        berth = _actor_reference_from_data(
            data.get("berth"), "docking event berth"
        )
        return DockingEventProjection(time, outcome, vessel, berth)


_DOCKING_EVENT_FORMAT_KEY = (
    ropemother.format.portableformat.PortableFormatKey.from_str(
        "harbor-docking-event"
    )
)

DOCKING_EVENT_PROJECTION_FORMAT = (
    ropemother.format.portableformat.PortableFormat(
        key=_DOCKING_EVENT_FORMAT_KEY,
        adapter=DockingEventProjectionAdapter(),
        serializer=ropemother.util.onelinejson.JSONL_SERIALIZER,
    )
)


class DockingRequestProcedureAdapter(
    ropemother.util.serializer.TypeAdapter[
        ropemother.client.procedure.ProcedureInvocation,
        ropemother.util.onelinejson.JSONRecord,
    ]
):

    def encode(
        self, value: ropemother.client.procedure.ProcedureInvocation
    ) -> ropemother.util.onelinejson.JSONRecord:
        if len(value.positional_arguments) != 2 or value.keyword_arguments:
            raise InvalidMessagePayloadError(
                "request_docking requires two positional arguments"
            )

        vessel, berth = value.positional_arguments
        if not isinstance(vessel, ActorReference):
            raise InvalidMessagePayloadError(
                "request_docking vessel requires an ActorReference"
            )
        if not isinstance(berth, ActorReference):
            raise InvalidMessagePayloadError(
                "request_docking berth requires an ActorReference"
            )
        return {"vessel": vessel.value, "berth": berth.value}

    def decode(
        self, data: ropemother.util.onelinejson.JSONRecord
    ) -> ropemother.client.procedure.ProcedureInvocation:
        vessel_data = data.get("vessel")
        berth_data = data.get("berth")
        if not isinstance(vessel_data, str) or not isinstance(berth_data, str):
            raise InvalidMessagePayloadError(
                "docking request actor references must be strings"
            )
        value = ropemother.client.procedure.ProcedureInvocation.from_call(
            ActorReference(vessel_data), ActorReference(berth_data)
        )
        return value


_DOCKING_REQUEST_FORMAT_KEY = (
    ropemother.format.portableformat.PortableFormatKey.from_str(
        "harbor-docking-request"
    )
)

DOCKING_REQUEST_PROCEDURE_FORMAT = (
    ropemother.format.portableformat.PortableFormat(
        key=_DOCKING_REQUEST_FORMAT_KEY,
        adapter=DockingRequestProcedureAdapter(),
        serializer=ropemother.util.onelinejson.JSONL_SERIALIZER,
    )
)


class AdvanceThroughProcedureAdapter(
    ropemother.util.serializer.TypeAdapter[
        ropemother.client.procedure.ProcedureInvocation,
        ropemother.util.onelinejson.JSONRecord,
    ]
):

    def encode(
        self, value: ropemother.client.procedure.ProcedureInvocation
    ) -> ropemother.util.onelinejson.JSONRecord:
        if len(value.positional_arguments) != 1 or value.keyword_arguments:
            raise InvalidMessagePayloadError(
                "advance_through requires one positional argument"
            )

        span = value.positional_arguments[0]
        if not isinstance(span, TimeSpan):
            raise InvalidMessagePayloadError(
                "advance_through requires a TimeSpan"
            )

        return {"start": span.start.value, "end": span.end.value}

    def decode(
        self, data: ropemother.util.onelinejson.JSONRecord
    ) -> ropemother.client.procedure.ProcedureInvocation:
        span = TimeSpan(Time(data["start"]), Time(data["end"]))
        return ropemother.client.procedure.ProcedureInvocation.from_call(span)


_ADVANCE_THROUGH_FORMAT_KEY = (
    ropemother.format.portableformat.PortableFormatKey.from_str(
        "harbor-advance-through"
    )
)

ADVANCE_THROUGH_PROCEDURE_FORMAT = (
    ropemother.format.portableformat.PortableFormat(
        key=_ADVANCE_THROUGH_FORMAT_KEY,
        adapter=AdvanceThroughProcedureAdapter(),
        serializer=ropemother.util.onelinejson.JSONL_SERIALIZER,
    )
)


class BeginBerthServiceProcedureAdapter(
    ropemother.util.serializer.TypeAdapter[
        ropemother.client.procedure.ProcedureInvocation,
        ropemother.util.onelinejson.JSONRecord,
    ]
):

    def encode(
        self, value: ropemother.client.procedure.ProcedureInvocation
    ) -> ropemother.util.onelinejson.JSONRecord:
        if len(value.positional_arguments) != 2 or value.keyword_arguments:
            raise InvalidMessagePayloadError(
                "begin_service requires two positional arguments"
            )

        start, duration = value.positional_arguments
        if not isinstance(start, Time):
            raise InvalidMessagePayloadError(
                "begin_service start requires a Time"
            )
        if not isinstance(duration, TimeDelta):
            raise InvalidMessagePayloadError(
                "begin_service duration requires a TimeDelta"
            )

        return {"start": start.value, "duration": duration.value}

    def decode(
        self, data: ropemother.util.onelinejson.JSONRecord
    ) -> ropemother.client.procedure.ProcedureInvocation:
        start = Time(data["start"])
        duration = TimeDelta(data["duration"])
        value = ropemother.client.procedure.ProcedureInvocation.from_call(
            start, duration
        )
        return value


_BEGIN_BERTH_SERVICE_FORMAT_KEY = (
    ropemother.format.portableformat.PortableFormatKey.from_str(
        "harbor-begin-berth-service"
    )
)

BEGIN_BERTH_SERVICE_PROCEDURE_FORMAT = (
    ropemother.format.portableformat.PortableFormat(
        key=_BEGIN_BERTH_SERVICE_FORMAT_KEY,
        adapter=BeginBerthServiceProcedureAdapter(),
        serializer=ropemother.util.onelinejson.JSONL_SERIALIZER,
    )
)


class NextTransitionTimeAdapter(
    ropemother.util.serializer.TypeAdapter[
        Time | None, ropemother.util.onelinejson.JSONPrimitive
    ]
):

    def encode(
        self, value: Time | None
    ) -> ropemother.util.onelinejson.JSONPrimitive:
        if value is None:
            return None
        return value.value

    def decode(
        self, data: ropemother.util.onelinejson.JSONPrimitive
    ) -> Time | None:
        if data is None:
            return None
        if isinstance(data, bool) or not isinstance(data, int | float):
            raise InvalidMessagePayloadError(
                "next transition time must be a JSON number or null"
            )
        return Time(data)


_NEXT_TRANSITION_TIME_FORMAT_KEY = (
    ropemother.format.portableformat.PortableFormatKey.from_str(
        "harbor-next-transition-time"
    )
)

NEXT_TRANSITION_TIME_FORMAT = ropemother.format.portableformat.PortableFormat(
    key=_NEXT_TRANSITION_TIME_FORMAT_KEY,
    adapter=NextTransitionTimeAdapter(),
    serializer=ropemother.util.onelinejson.JSONL_SERIALIZER,
)


class HarborStateProjectionAdapter(
    ropemother.util.serializer.TypeAdapter[
        HarborStateProjection,
        ropemother.util.onelinejson.JSONRecord,
    ]
):

    def encode(
        self, value: HarborStateProjection
    ) -> ropemother.util.onelinejson.JSONRecord:
        vessels = [_vessel_state_record(vessel) for vessel in value.vessels]
        berths = [_berth_state_record(berth) for berth in value.berths]
        facilities = [
            _facility_state_record(facility) for facility in value.facilities
        ]
        data = {
            "time": value.time.value,
            "vessels": vessels,
            "berths": berths,
            "facilities": facilities,
        }
        return data

    def decode(
        self, data: ropemother.util.onelinejson.JSONRecord
    ) -> HarborStateProjection:
        time = _time_from_data(data.get("time"), "harbor state time")
        vessel_records = _record_list(
            data.get("vessels"), "harbor state vessels"
        )
        berth_records = _record_list(data.get("berths"), "harbor state berths")
        facility_records = _record_list(
            data.get("facilities"), "harbor state facilities"
        )
        vessels = tuple(
            _vessel_state_from_record(record) for record in vessel_records
        )
        berths = tuple(
            _berth_state_from_record(record) for record in berth_records
        )
        facilities = tuple(
            _facility_state_from_record(record) for record in facility_records
        )
        return HarborStateProjection(time, vessels, berths, facilities)


_HARBOR_STATE_PROJECTION_FORMAT_KEY = (
    ropemother.format.portableformat.PortableFormatKey.from_str(
        "harbor-state-projection"
    )
)

HARBOR_STATE_PROJECTION_FORMAT = (
    ropemother.format.portableformat.PortableFormat(
        key=_HARBOR_STATE_PROJECTION_FORMAT_KEY,
        adapter=HarborStateProjectionAdapter(),
        serializer=ropemother.util.onelinejson.JSONL_SERIALIZER,
    )
)


class TransitClearanceProjectionAdapter(
    ropemother.util.serializer.TypeAdapter[
        TransitClearanceProjection,
        ropemother.util.onelinejson.JSONRecord,
    ]
):

    def encode(
        self, value: TransitClearanceProjection
    ) -> ropemother.util.onelinejson.JSONRecord:
        start_spans = [_time_span_record(span) for span in value.start_spans]
        data = {
            "evaluated_at": value.evaluated_at.value,
            "vessel": value.vessel.value,
            "within": _time_span_record(value.within),
            "start_spans": start_spans,
        }
        return data

    def decode(
        self, data: ropemother.util.onelinejson.JSONRecord
    ) -> TransitClearanceProjection:
        evaluated_at = _time_from_data(
            data.get("evaluated_at"), "transit clearance evaluation time"
        )
        vessel_data = data.get("vessel")
        if not isinstance(vessel_data, str):
            raise InvalidMessagePayloadError(
                "transit clearance vessel must be a string"
            )
        within = _time_span_from_data(
            data.get("within"), "transit clearance interval"
        )
        span_data = _record_list(
            data.get("start_spans"), "transit clearance start spans"
        )
        start_spans = tuple(
            _time_span_from_data(data, "transit clearance start span")
            for data in span_data
        )
        value = TransitClearanceProjection(
            evaluated_at, ActorReference(vessel_data), within, start_spans
        )
        return value


_TRANSIT_CLEARANCE_PROJECTION_FORMAT_KEY = (
    ropemother.format.portableformat.PortableFormatKey.from_str(
        "harbor-transit-clearance-projection"
    )
)

TRANSIT_CLEARANCE_PROJECTION_FORMAT = (
    ropemother.format.portableformat.PortableFormat(
        key=_TRANSIT_CLEARANCE_PROJECTION_FORMAT_KEY,
        adapter=TransitClearanceProjectionAdapter(),
        serializer=ropemother.util.onelinejson.JSONL_SERIALIZER,
    )
)


def _vessel_state_record(
    vessel: VesselStateProjection,
) -> ropemother.util.onelinejson.JSONRecord:
    motion_span = None
    if vessel.motion_span is not None:
        motion_span = _time_span_record(vessel.motion_span)

    record = {
        "vessel": vessel.vessel.value,
        "position": _position_data(vessel.position),
        "orientation": vessel.orientation.value,
        "draft": vessel.draft.value,
        "motion_span": motion_span,
        "itinerary_complete": vessel.itinerary_complete,
    }
    return record


def _vessel_state_from_record(
    record: ropemother.util.onelinejson.JSONRecord,
) -> VesselStateProjection:
    vessel = _actor_reference_from_data(
        record.get("vessel"), "vessel state vessel"
    )
    position = _position_from_data(
        record.get("position"), "vessel state position"
    )
    orientation = Orientation(
        _number_from_data(
            record.get("orientation"), "vessel state orientation"
        )
    )
    draft = Distance(
        _number_from_data(record.get("draft"), "vessel state draft")
    )

    motion_span_data = record.get("motion_span")
    motion_span = None
    if motion_span_data is not None:
        motion_span = _time_span_from_data(
            motion_span_data, "vessel state motion span"
        )

    itinerary_complete = _boolean_from_data(
        record.get("itinerary_complete"), "vessel state itinerary completion"
    )
    projection = VesselStateProjection(
        vessel,
        position,
        orientation,
        draft,
        motion_span,
        itinerary_complete,
    )
    return projection


def _berth_state_record(
    berth: BerthStateProjection,
) -> ropemother.util.onelinejson.JSONRecord:
    authorized_vessel = None
    if berth.authorized_vessel is not None:
        authorized_vessel = berth.authorized_vessel.value

    docked_vessel = None
    if berth.docked_vessel is not None:
        docked_vessel = berth.docked_vessel.value

    service = None
    if berth.service is not None:
        service = {
            "span": _time_span_record(berth.service.span),
            "complete": berth.service.complete,
        }

    record = {
        "berth": berth.berth.value,
        "authorized_vessel": authorized_vessel,
        "docked_vessel": docked_vessel,
        "service": service,
    }
    return record


def _berth_state_from_record(
    record: ropemother.util.onelinejson.JSONRecord,
) -> BerthStateProjection:
    berth = _actor_reference_from_data(
        record.get("berth"), "berth state berth"
    )

    authorized_vessel_data = record.get("authorized_vessel")
    authorized_vessel = None
    if authorized_vessel_data is not None:
        authorized_vessel = _actor_reference_from_data(
            authorized_vessel_data, "berth state authorized vessel"
        )

    docked_vessel_data = record.get("docked_vessel")
    docked_vessel = None
    if docked_vessel_data is not None:
        docked_vessel = _actor_reference_from_data(
            docked_vessel_data, "berth state docked vessel"
        )

    service_data = record.get("service")
    service = None
    if service_data is not None:
        if not isinstance(service_data, dict):
            raise InvalidMessagePayloadError(
                "berth state service must be a JSON object"
            )
        span = _time_span_from_data(
            service_data.get("span"), "berth state service span"
        )
        complete = _boolean_from_data(
            service_data.get("complete"), "berth state service completion"
        )
        service = BerthServiceProjection(span, complete)

    projection = BerthStateProjection(
        berth, authorized_vessel, docked_vessel, service
    )
    return projection


def _facility_state_record(
    facility: FacilityStateProjection,
) -> ropemother.util.onelinejson.JSONRecord:
    berths = [berth.value for berth in facility.berths]
    record = {
        "facility": facility.facility.value,
        "position": _position_data(facility.position),
        "orientation": facility.orientation.value,
        "berths": berths,
    }
    return record


def _facility_state_from_record(
    record: ropemother.util.onelinejson.JSONRecord,
) -> FacilityStateProjection:
    facility = _actor_reference_from_data(
        record.get("facility"), "facility state facility"
    )
    position = _position_from_data(
        record.get("position"), "facility state position"
    )
    orientation = Orientation(
        _number_from_data(
            record.get("orientation"), "facility state orientation"
        )
    )

    berth_data = record.get("berths")
    if not isinstance(berth_data, list):
        raise InvalidMessagePayloadError(
            "facility state berths must be a JSON array"
        )
    berths = tuple(
        _actor_reference_from_data(data, "facility state berth")
        for data in berth_data
    )

    return FacilityStateProjection(facility, position, orientation, berths)


def _actor_reference_from_data(
    data: ropemother.util.onelinejson.JSONValue, description: str
) -> ActorReference:
    if not isinstance(data, str):
        raise InvalidMessagePayloadError(f"{description} must be a string")
    return ActorReference(data)


def _position_data(
    position: Position,
) -> list[ropemother.util.onelinejson.JSONValue]:
    return [coordinate.value for coordinate in position.point.coordinates]


def _position_from_data(
    data: ropemother.util.onelinejson.JSONValue, description: str
) -> Position:
    if not isinstance(data, list) or len(data) != 2:
        raise InvalidMessagePayloadError(
            f"{description} must be a two-number JSON array"
        )
    x = _number_from_data(data[0], f"{description} x")
    y = _number_from_data(data[1], f"{description} y")
    return Position.from_components(x, y)


def _time_span_record(
    span: TimeSpan,
) -> ropemother.util.onelinejson.JSONRecord:
    return {"start": span.start.value, "end": span.end.value}


def _time_span_from_data(
    data: ropemother.util.onelinejson.JSONValue, description: str
) -> TimeSpan:
    if not isinstance(data, dict):
        raise InvalidMessagePayloadError(
            f"{description} must be a JSON object"
        )
    start = _time_from_data(data.get("start"), f"{description} start")
    end = _time_from_data(data.get("end"), f"{description} end")
    return TimeSpan(start, end)


def _time_from_data(
    data: ropemother.util.onelinejson.JSONValue, description: str
) -> Time:
    return Time(_number_from_data(data, description))


def _number_from_data(
    data: ropemother.util.onelinejson.JSONValue, description: str
) -> int | float:
    if isinstance(data, bool) or not isinstance(data, int | float):
        raise InvalidMessagePayloadError(f"{description} must be numeric")
    return data


def _boolean_from_data(
    data: ropemother.util.onelinejson.JSONValue, description: str
) -> bool:
    if not isinstance(data, bool):
        raise InvalidMessagePayloadError(f"{description} must be a boolean")
    return data


def _record_list(
    data: ropemother.util.onelinejson.JSONValue, description: str
) -> tuple[ropemother.util.onelinejson.JSONRecord, ...]:
    if not isinstance(data, list) or not all(
        isinstance(record, dict) for record in data
    ):
        raise InvalidMessagePayloadError(
            f"{description} must be a JSON array of objects"
        )
    return tuple(data)
