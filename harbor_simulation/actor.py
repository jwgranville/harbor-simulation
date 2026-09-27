#!/usr/bin/env python3
# harbor_simulation/actor.py

import abc

from harbor_simulation.quantitative import Time, TimeSpan

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-15T19:03:37+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


class Actor(abc.ABC):

    @abc.abstractmethod
    def advance_through(self, span: TimeSpan) -> None:
        pass

    @abc.abstractmethod
    def next_transition_time(self) -> Time | None:
        pass
