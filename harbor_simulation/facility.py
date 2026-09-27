#!/usr/bin/env python3
# harbor_simulation/facility.py

import dataclasses

from harbor_simulation.actor import Actor
from harbor_simulation.berth import Berth
from harbor_simulation.quantitative import Time, TimeSpan
from harbor_simulation.spatial import Presence
from harbor_simulation.vessel import Vessel

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-18T17:21:00+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


@dataclasses.dataclass(eq=False)
class Facility(Actor):
    presence: Presence
    berths: tuple[Berth, ...]

    def request_docking(
        self, vessel: Vessel, berth: Berth
    ) -> "DockingAuthorized | DockingRequestRejected":
        if berth not in self.berths or not berth.is_available():
            return DockingRequestRejected(vessel, berth)
        berth.approve_docking(vessel)
        return DockingAuthorized(vessel, berth)

    def advance_through(self, span: TimeSpan) -> None:
        pass

    def next_transition_time(self) -> Time | None:
        return None


@dataclasses.dataclass(frozen=True)
class DockingAuthorized:
    vessel: Vessel
    berth: Berth


@dataclasses.dataclass(frozen=True)
class DockingRequestRejected:
    vessel: Vessel
    berth: Berth
