#!/usr/bin/env python3
# tests/unit/test_projection.py

import pytest

from harbor_simulation.berth import Berth
from harbor_simulation.exceptions import InvalidProjectionError
from harbor_simulation.facility import (
    DockingAuthorized,
    DockingRequestRejected,
    Facility,
)
from harbor_simulation.projection import (
    ActorReference,
    BerthServiceProjection,
    BerthStateProjection,
    DockingEventProjection,
    DockingEventProjector,
    DockingOutcome,
    FacilityStateProjection,
    HarborStateProjection,
    HarborStateProjector,
    VesselStateProjection,
)
from harbor_simulation.quantitative import Time, TimeDelta, TimeSpan
from harbor_simulation.vessel import Vessel

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-26T18:07:08+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def test_harbor_state_projects_actor_state(
    vessel: Vessel, berth: Berth, facility: Facility
) -> None:
    vessel_reference = ActorReference("vessel-a")
    berth_reference = ActorReference("berth-a")
    facility_reference = ActorReference("facility-a")
    references = {
        vessel: vessel_reference,
        berth: berth_reference,
        facility: facility_reference,
    }
    projector = HarborStateProjector(references)

    facility.request_docking(vessel, berth)
    berth.dock(vessel)
    berth.begin_service(Time(0), TimeDelta(5))

    projection = projector.project(Time(2), (facility, berth, vessel))

    expected_vessel = VesselStateProjection(
        vessel_reference,
        vessel.presence.position,
        vessel.presence.orientation,
        vessel.draft,
        vessel.motion.span,
        False,
    )
    expected_service = BerthServiceProjection(
        TimeSpan.from_values(0, 5), False
    )
    expected_berth = BerthStateProjection(
        berth_reference,
        vessel_reference,
        vessel_reference,
        expected_service,
    )
    expected_facility = FacilityStateProjection(
        facility_reference,
        facility.presence.position,
        facility.presence.orientation,
        (berth_reference,),
    )
    expected = HarborStateProjection(
        Time(2), (expected_vessel,), (expected_berth,), (expected_facility,)
    )

    assert projection == expected


def test_harbor_state_projection_is_a_snapshot(
    vessel: Vessel, berth: Berth, facility: Facility
) -> None:
    references = {
        vessel: ActorReference("vessel-a"),
        berth: ActorReference("berth-a"),
        facility: ActorReference("facility-a"),
    }
    projector = HarborStateProjector(references)

    facility.request_docking(vessel, berth)
    berth.dock(vessel)
    berth.begin_service(Time(0), TimeDelta(5))
    projection = projector.project(Time(0), (vessel, berth, facility))

    vessel.advance_through(TimeSpan.from_values(0, 5))
    berth.advance_through(TimeSpan.from_values(0, 5))

    assert projection.vessels[0].position != vessel.presence.position
    assert projection.berths[0].service == BerthServiceProjection(
        TimeSpan.from_values(0, 5), False
    )
    assert berth.service is not None
    assert berth.service.complete


def test_harbor_state_projection_requires_actor_reference(
    vessel: Vessel,
) -> None:
    projector = HarborStateProjector({})

    with pytest.raises(InvalidProjectionError):
        projector.project(Time(0), (vessel,))


def test_docking_events_project_outcomes(vessel: Vessel, berth: Berth) -> None:
    vessel_reference = ActorReference("vessel-a")
    berth_reference = ActorReference("berth-a")
    projector = DockingEventProjector(
        {vessel: vessel_reference, berth: berth_reference}
    )

    authorization = projector.project(
        Time(2), DockingAuthorized(vessel, berth)
    )
    rejection = projector.project(
        Time(3), DockingRequestRejected(vessel, berth)
    )

    assert authorization == DockingEventProjection(
        Time(2), DockingOutcome.AUTHORIZED, vessel_reference, berth_reference
    )
    assert rejection == DockingEventProjection(
        Time(3), DockingOutcome.REJECTED, vessel_reference, berth_reference
    )


def test_docking_event_projection_requires_actor_reference(
    vessel: Vessel, berth: Berth
) -> None:
    projector = DockingEventProjector({vessel: ActorReference("vessel-a")})

    with pytest.raises(InvalidProjectionError):
        projector.project(Time(0), DockingAuthorized(vessel, berth))
