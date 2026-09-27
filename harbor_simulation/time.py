#!/usr/bin/env python3
# harbor_simulation/time.py

import dataclasses

from harbor_simulation.exceptions import OutOfDomainError
from harbor_simulation.quantitative import Time, TimeDelta, TimeSpan

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-13T22:24:33+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


@dataclasses.dataclass
class Clock:
    time: Time

    def advance_to(self, time: Time) -> TimeSpan:
        if time < self.time:
            raise OutOfDomainError

        span = TimeSpan(self.time, time)
        self.time = time
        return span

    def advance_by(self, delta: TimeDelta) -> TimeSpan:
        return self.advance_to(self.time + delta)


@dataclasses.dataclass
class Schedule[T]:
    entries: dict[Time, list[T]] = dataclasses.field(default_factory=dict)

    def add(self, time: Time, item: T) -> None:
        self.entries.setdefault(time, []).append(item)

    def next_time(self) -> Time | None:
        if self.entries:
            return min(self.entries)
        return None

    def pop_at(self, time: Time) -> tuple[T, ...]:
        items = self.entries.pop(time, None)
        if items is None:
            return ()
        return tuple(items)


@dataclasses.dataclass
class Timeline[T]:
    clock: Clock
    schedule: Schedule[T]

    def advance_toward(self, target: Time) -> TimeSpan:
        stop = target
        scheduled = self.schedule.next_time()

        if scheduled is not None and scheduled <= target:
            stop = scheduled

        return self.clock.advance_to(stop)

    def pop_due(self) -> tuple[T, ...]:
        return self.schedule.pop_at(self.clock.time)
