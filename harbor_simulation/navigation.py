#!/usr/bin/env python3
# harbor_simulation/navigation.py

import dataclasses

from harbor_simulation.exceptions import InvalidVesselOperationError
from harbor_simulation.plan import LinearLeg
from harbor_simulation.quantitative import Distance, Time, TimeSpan
from harbor_simulation.terrain import TerrainSurface
from harbor_simulation.vessel import Vessel
from harbor_simulation.water import UniformHarmonicWaterLevel

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-22T17:06:39+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


@dataclasses.dataclass(frozen=True)
class UnderKeelClearanceConstraint:
    required_clearance: Distance

    def available_clearance(
        self, vessel: Vessel, water_depth: Distance
    ) -> Distance:
        return water_depth - vessel.draft

    def is_satisfied_by(self, vessel: Vessel, water_depth: Distance) -> bool:
        clearance = self.available_clearance(vessel, water_depth)
        return self.required_clearance <= clearance

    def required_water_depth(self, vessel: Vessel) -> Distance:
        return vessel.draft + self.required_clearance

    def required_water_level(
        self, vessel: Vessel, terrain_elevation: Distance
    ) -> Distance:
        return terrain_elevation + self.required_water_depth(vessel)


@dataclasses.dataclass(frozen=True)
class ConservativeTransitClearanceModel:
    terrain: TerrainSurface
    water_level: UniformHarmonicWaterLevel
    constraint: UnderKeelClearanceConstraint

    def start_spans_for(
        self, vessel: Vessel, within: TimeSpan
    ) -> tuple[TimeSpan, ...]:
        leg = self._pending_leg_for(vessel)
        displacement = leg.destination - vessel.presence.position
        swept = vessel.presence.region().swept_by(displacement)
        terrain_elevation = self.terrain.maximum_elevation_within(swept)
        if terrain_elevation is None:
            return ()

        required_level = self.constraint.required_water_level(
            vessel, terrain_elevation
        )
        clearance_spans = self.water_level.spans_at_or_above(
            required_level, within
        )
        start_spans = tuple(
            start_span
            for span in clearance_spans
            if (start_span := span.start_times_for(leg.duration)) is not None
        )
        return start_spans

    def permits_start_at(self, vessel: Vessel, time: Time) -> bool:
        duration = self._pending_leg_for(vessel).duration
        within = TimeSpan(time, time + duration)
        permitted = any(
            time in span for span in self.start_spans_for(vessel, within)
        )
        return permitted

    @staticmethod
    def _pending_leg_for(vessel: Vessel) -> LinearLeg:
        if vessel.motion is not None or vessel.plan_state.is_complete():
            raise InvalidVesselOperationError("itinerary is not pending")
        return vessel.plan_state.current_leg()
