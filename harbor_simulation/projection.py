#!/usr/bin/env python3
# harbor_simulation/projection.py

import collections.abc
import dataclasses
import enum

from harbor_simulation.actor import Actor
from harbor_simulation.berth import Berth, BerthService
from harbor_simulation.exceptions import InvalidProjectionError
from harbor_simulation.facility import (
    DockingAuthorized,
    DockingRequestRejected,
    Facility,
)
from harbor_simulation.navigation import ConservativeTransitClearanceModel
from harbor_simulation.quantitative import Distance, Position, Time, TimeSpan
from harbor_simulation.spatial import Orientation
from harbor_simulation.vessel import Vessel

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-27T23:57:01+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


@dataclasses.dataclass(frozen=True)
class ActorReference:
    value: str


class DockingOutcome(enum.StrEnum):
    AUTHORIZED = "authorized"
    REJECTED = "rejected"


@dataclasses.dataclass(frozen=True)
class DockingEventProjection:
    time: Time
    outcome: DockingOutcome
    vessel: ActorReference
    berth: ActorReference


@dataclasses.dataclass(frozen=True)
class VesselStateProjection:
    vessel: ActorReference
    position: Position
    orientation: Orientation
    draft: Distance
    motion_span: TimeSpan | None
    itinerary_complete: bool


@dataclasses.dataclass(frozen=True)
class BerthServiceProjection:
    span: TimeSpan
    complete: bool


@dataclasses.dataclass(frozen=True)
class BerthStateProjection:
    berth: ActorReference
    authorized_vessel: ActorReference | None
    docked_vessel: ActorReference | None
    service: BerthServiceProjection | None


@dataclasses.dataclass(frozen=True)
class FacilityStateProjection:
    facility: ActorReference
    position: Position
    orientation: Orientation
    berths: tuple[ActorReference, ...]


@dataclasses.dataclass(frozen=True)
class HarborStateProjection:
    time: Time
    vessels: tuple[VesselStateProjection, ...]
    berths: tuple[BerthStateProjection, ...]
    facilities: tuple[FacilityStateProjection, ...]


@dataclasses.dataclass(frozen=True)
class TransitClearanceProjection:
    evaluated_at: Time
    vessel: ActorReference
    within: TimeSpan
    start_spans: tuple[TimeSpan, ...]


@dataclasses.dataclass(frozen=True)
class SimulationRunCompletedProjection:
    time: Time


@dataclasses.dataclass(frozen=True)
class HarborStateProjector:
    actor_references: collections.abc.Mapping[Actor, ActorReference]

    def project(
        self, time: Time, actors: collections.abc.Iterable[Actor]
    ) -> HarborStateProjection:
        vessels = []
        berths = []
        facilities = []

        for actor in actors:
            if isinstance(actor, Vessel):
                vessels.append(self._project_vessel(actor))
            elif isinstance(actor, Berth):
                berths.append(self._project_berth(actor))
            elif isinstance(actor, Facility):
                facilities.append(self._project_facility(actor))
            else:
                raise InvalidProjectionError(
                    f"unsupported actor type: {type(actor).__name__}"
                )

        projection = HarborStateProjection(
            time, tuple(vessels), tuple(berths), tuple(facilities)
        )
        return projection

    def _project_vessel(self, vessel: Vessel) -> VesselStateProjection:
        motion_span = vessel.motion.span if vessel.motion is not None else None
        projection = VesselStateProjection(
            self._reference_for(vessel),
            vessel.presence.position,
            vessel.presence.orientation,
            vessel.draft,
            motion_span,
            vessel.plan_state.is_complete(),
        )
        return projection

    def _project_berth(self, berth: Berth) -> BerthStateProjection:
        service = self._project_service(berth.service)
        projection = BerthStateProjection(
            self._reference_for(berth),
            self._optional_reference(berth.authorized_vessel),
            self._optional_reference(berth.docked_vessel),
            service,
        )
        return projection

    def _project_facility(self, facility: Facility) -> FacilityStateProjection:
        berths = tuple(self._reference_for(berth) for berth in facility.berths)
        projection = FacilityStateProjection(
            self._reference_for(facility),
            facility.presence.position,
            facility.presence.orientation,
            berths,
        )
        return projection

    def _reference_for(self, actor: Actor) -> ActorReference:
        reference = self.actor_references.get(actor)
        if reference is None:
            raise InvalidProjectionError(
                f"actor has no reference: {type(actor).__name__}"
            )
        return reference

    def _optional_reference(
        self, actor: Actor | None
    ) -> ActorReference | None:
        if actor is None:
            return None
        return self._reference_for(actor)

    @staticmethod
    def _project_service(
        service: BerthService | None,
    ) -> BerthServiceProjection | None:
        if service is None:
            return None
        return BerthServiceProjection(service.span, service.complete)


@dataclasses.dataclass(frozen=True)
class DockingEventProjector:
    actor_references: collections.abc.Mapping[Actor, ActorReference]

    def project(
        self, time: Time, event: DockingAuthorized | DockingRequestRejected
    ) -> DockingEventProjection:
        if isinstance(event, DockingAuthorized):
            outcome = DockingOutcome.AUTHORIZED
        else:
            outcome = DockingOutcome.REJECTED

        vessel_reference = self.actor_references.get(event.vessel)
        if vessel_reference is None:
            raise InvalidProjectionError(
                "docking event vessel has no reference"
            )
        berth_reference = self.actor_references.get(event.berth)
        if berth_reference is None:
            raise InvalidProjectionError(
                "docking event berth has no reference"
            )

        projection = DockingEventProjection(
            time, outcome, vessel_reference, berth_reference
        )
        return projection


@dataclasses.dataclass(frozen=True)
class TransitClearanceProjector:
    actor_references: collections.abc.Mapping[Actor, ActorReference]
    clearance: ConservativeTransitClearanceModel

    def project(
        self, evaluated_at: Time, vessel: Vessel, within: TimeSpan
    ) -> TransitClearanceProjection:
        vessel_reference = self.actor_references.get(vessel)
        if vessel_reference is None:
            raise InvalidProjectionError("vessel has no actor reference")

        start_spans = self.clearance.start_spans_for(vessel, within)
        projection = TransitClearanceProjection(
            evaluated_at, vessel_reference, within, start_spans
        )
        return projection
