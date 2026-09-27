#!/usr/bin/env python3
# harbor_simulation/berth.py

import dataclasses

from harbor_simulation.actor import Actor
from harbor_simulation.exceptions import InvalidBerthOperationError
from harbor_simulation.quantitative import Time, TimeDelta, TimeSpan
from harbor_simulation.spatial import (
    Extent,
    GlobalPlacement,
    LocalPlacement,
    Region,
)
from harbor_simulation.vessel import Vessel

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-22T01:06:23+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


@dataclasses.dataclass
class BerthService:
    span: TimeSpan
    complete: bool = False


@dataclasses.dataclass(eq=False)
class Berth(Actor):
    placement: LocalPlacement
    working_extent: Extent
    authorized_vessel: Vessel | None = None
    docked_vessel: Vessel | None = None
    service: BerthService | None = None

    def working_region_at(self, host: GlobalPlacement) -> Region:
        placement = host.place(self.placement)
        return self.working_extent.region_at(placement)

    def is_available(self) -> bool:
        return self.authorized_vessel is None and self.docked_vessel is None

    def approve_docking(self, vessel: Vessel) -> None:
        if not self.is_available():
            raise InvalidBerthOperationError("berth is not available")
        self.authorized_vessel = vessel

    def dock(self, vessel: Vessel) -> None:
        if self.authorized_vessel is not vessel:
            raise InvalidBerthOperationError(
                "vessel is not authorized to dock"
            )
        self.docked_vessel = vessel

    def begin_service(self, start: Time, duration: TimeDelta) -> None:
        if self.docked_vessel is None:
            raise InvalidBerthOperationError(
                "service requires a docked vessel"
            )
        self.service = BerthService(TimeSpan(start, start + duration))

    def depart(self, vessel: Vessel) -> None:
        if self.docked_vessel is not vessel:
            raise InvalidBerthOperationError(
                "vessel is not docked at this berth"
            )
        if self.service is not None and not self.service.complete:
            raise InvalidBerthOperationError(
                "vessel cannot depart during service"
            )
        self.authorized_vessel = None
        self.docked_vessel = None
        self.service = None

    def advance_through(self, span: TimeSpan) -> None:
        if (
            self.service is not None
            and not self.service.complete
            and span.end == self.service.span.end
        ):
            self.service.complete = True

    def next_transition_time(self) -> Time | None:
        if self.service is not None and not self.service.complete:
            return self.service.span.end
        return None
