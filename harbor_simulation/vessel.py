#!/usr/bin/env python3
# harbor_simulation/vessel.py

import dataclasses

from harbor_simulation.actor import Actor
from harbor_simulation.exceptions import InvalidVesselOperationError
from harbor_simulation.kinematics import LinearMotion
from harbor_simulation.plan import Itinerary, ItineraryState
from harbor_simulation.quantitative import Distance, Position, Time, TimeSpan
from harbor_simulation.spatial import Presence

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-23T02:35:02+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


@dataclasses.dataclass(eq=False)
class Vessel(Actor):
    presence: Presence
    draft: Distance
    plan_state: ItineraryState
    motion: LinearMotion | None

    def advance_through(self, span: TimeSpan) -> None:
        if self.motion is not None:
            position = self.motion.position_at(span.end)
            self.presence.position = position

            if span.end == self.motion.span.end:
                self.advance_itinerary(position, span.end)

    def advance_itinerary(self, position: Position, time: Time) -> None:
        self.plan_state.advance()

        if self.plan_state.is_complete():
            self.motion = None
        else:
            leg = self.plan_state.current_leg()
            self.motion = leg.manifest(position, time)

    def next_transition_time(self) -> Time | None:
        if self.motion is not None:
            return self.motion.span.end
        return None

    def begin_itinerary(self, time: Time) -> None:
        if self.motion is not None:
            raise InvalidVesselOperationError("itinerary is already underway")
        if self.plan_state.is_complete():
            raise InvalidVesselOperationError("itinerary is already complete")

        leg = self.plan_state.current_leg()
        self.motion = leg.manifest(self.presence.position, time)

    @classmethod
    def from_itinerary(
        cls, presence: Presence, itinerary: Itinerary, draft: Distance
    ) -> "Vessel":
        return cls(presence, draft, ItineraryState(itinerary), None)
