#!/usr/bin/env python3
# harbor_simulation/temporal.py

import abc
import dataclasses

from harbor_simulation.quantitative import Time, TimeSpan
from harbor_simulation.time import Timeline

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-26T19:33:37+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


@dataclasses.dataclass
class TemporalCoordinator[T]:
    timeline: Timeline[T]
    actor_facade: "ActorFacade"

    async def advance_toward(
        self, target: Time
    ) -> tuple[TimeSpan, tuple[T, ...]]:
        transition_time = await self.actor_facade.next_transition_time()

        if transition_time is not None and transition_time < target:
            target = transition_time

        span = self.timeline.advance_toward(target)

        if span.start != span.end:
            await self.actor_facade.advance_through(span)

        return span, self.timeline.pop_due()


class ActorFacade(abc.ABC):

    @abc.abstractmethod
    async def next_transition_time(self) -> Time | None:
        pass

    @abc.abstractmethod
    async def advance_through(self, span: TimeSpan) -> None:
        pass
