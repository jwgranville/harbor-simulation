#!/usr/bin/env python3
# harbor_simulation/plan.py

import dataclasses
import numbers

from harbor_simulation.kinematics import LinearMotion
from harbor_simulation.quantitative import Position, Time, TimeDelta, TimeSpan

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-16T16:07:31+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


@dataclasses.dataclass(frozen=True)
class LinearLeg:
    destination: Position
    duration: TimeDelta

    def manifest(self, initial: Position, start: Time) -> LinearMotion:
        displacement = self.destination - initial
        velocity = displacement / self.duration
        span = TimeSpan(start, start + self.duration)
        return LinearMotion(initial, velocity, span)

    def manifest_from_coordinates(
        self, initial: tuple[numbers.Real, numbers.Real], start: numbers.Real
    ) -> LinearMotion:
        return self.manifest(Position.from_components(*initial), Time(start))

    @classmethod
    def from_coordinates(
        cls,
        coordinates: tuple[numbers.Real, numbers.Real],
        duration: numbers.Real,
    ) -> "LinearLeg":
        return cls(Position.from_components(*coordinates), TimeDelta(duration))


@dataclasses.dataclass(frozen=True)
class Itinerary:
    legs: tuple[LinearLeg, ...]

    @classmethod
    def from_legs(cls, *legs: LinearLeg) -> "Itinerary":
        return cls(legs)


@dataclasses.dataclass
class ItineraryState:
    itinerary: Itinerary
    current_index: int = 0

    def current_leg(self) -> LinearLeg:
        return self.itinerary.legs[self.current_index]

    def is_complete(self) -> bool:
        return self.current_index >= len(self.itinerary.legs)

    def advance(self) -> None:
        self.current_index += 1
