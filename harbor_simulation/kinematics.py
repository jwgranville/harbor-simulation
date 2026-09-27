#!/usr/bin/env python3
# harbor_simulation/kinematics.py

import dataclasses

from harbor_simulation.exceptions import OutOfDomainError
from harbor_simulation.quantitative import (
    Displacement,
    Position,
    Time,
    TimeSpan,
    Velocity,
)

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-21T03:14:17+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


@dataclasses.dataclass(frozen=True)
class LinearMotion:
    initial: Position
    velocity: Velocity
    span: TimeSpan

    def position_at(self, time: Time) -> Position:
        if time not in self.span:
            raise OutOfDomainError

        elapsed = time - self.span.start
        displacement = self.velocity * elapsed
        return self.initial + displacement

    def displacement(self) -> Displacement:
        return self.velocity * self.span.duration
