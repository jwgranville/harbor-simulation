#!/usr/bin/env python3
# harbor_simulation/water.py

import abc
import dataclasses
import math

from harbor_simulation.exceptions import OutOfDomainError
from harbor_simulation.quantitative import (
    Distance,
    Position,
    Scalar,
    Time,
    TimeDelta,
    TimeSpan,
)
from harbor_simulation.spatial import RectangularRegion
from harbor_simulation.terrain import TerrainSurface

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-21T02:43:00+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


class WaterLevelModel(abc.ABC):
    @abc.abstractmethod
    def water_level_at(self, position: Position, time: Time) -> Distance:
        pass


class UniformWaterLevelModel(WaterLevelModel):
    def water_level_at(self, position: Position, time: Time) -> Distance:
        return self.water_level_at_time(time)

    @abc.abstractmethod
    def water_level_at_time(self, time: Time) -> Distance:
        pass


@dataclasses.dataclass(frozen=True)
class UniformHarmonicWaterLevel(UniformWaterLevelModel):
    mean_level: Distance
    amplitude: Distance
    period: TimeDelta
    high_water_time: Time

    def __post_init__(self) -> None:
        if self.amplitude < Distance(0) or self.period.value <= 0:
            raise OutOfDomainError

    def water_level_at_time(self, time: Time) -> Distance:
        elapsed = time - self.high_water_time
        phase = elapsed / self.period
        angle = 2 * math.pi * phase.value
        offset = self.amplitude * Scalar(math.cos(angle))
        return self.mean_level + offset

    def spans_at_or_above(
        self, level: Distance, within: TimeSpan
    ) -> tuple[TimeSpan, ...]:
        amplitude = self.amplitude.value
        if math.isclose(amplitude, 0):
            if level <= self.mean_level:
                return (within,)
            return ()

        threshold = (level.value - self.mean_level.value) / amplitude
        if threshold < -1 or math.isclose(threshold, -1):
            return (within,)
        if threshold > 1 and not math.isclose(threshold, 1):
            return ()

        threshold = min(1.0, max(-1.0, threshold))
        phase = math.acos(threshold) / (2 * math.pi)
        half_window = self.period * Scalar(phase)
        first_offset = within.start - half_window - self.high_water_time
        last_offset = within.end + half_window - self.high_water_time
        first_cycle = math.ceil((first_offset / self.period).value)
        last_cycle = math.floor((last_offset / self.period).value)
        spans = []

        for cycle in range(first_cycle, last_cycle + 1):
            peak = self.high_water_time + self.period * Scalar(cycle)
            start = max(peak - half_window, within.start)
            end = min(peak + half_window, within.end)
            spans.append(TimeSpan(start, end))

        return tuple(spans)


@dataclasses.dataclass(frozen=True)
class WaterDepthModel:
    terrain: TerrainSurface
    water_level: WaterLevelModel

    def depth_at(self, position: Position, time: Time) -> Distance | None:
        elevation = self.terrain.elevation_at(position)
        if elevation is None:
            return None
        level = self.water_level.water_level_at(position, time)
        return level - elevation


@dataclasses.dataclass(frozen=True)
class UniformLevelWaterDepthModel(WaterDepthModel):
    water_level: UniformWaterLevelModel

    def minimum_depth_within(
        self, region: RectangularRegion, time: Time
    ) -> Distance | None:
        elevation = self.terrain.maximum_elevation_within(region)
        if elevation is None:
            return None
        level = self.water_level.water_level_at_time(time)
        return level - elevation
