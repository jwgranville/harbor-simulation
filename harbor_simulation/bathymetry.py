#!/usr/bin/env python3
# harbor_simulation/bathymetry.py

import dataclasses

from harbor_simulation.quantitative import Distance, Position
from harbor_simulation.terrain import TerrainSurface

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-19T17:48:52+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


@dataclasses.dataclass(frozen=True)
class Bathymetry:
    terrain: TerrainSurface
    chart_datum: Distance

    def charted_depth_at(self, position: Position) -> Distance | None:
        elevation = self.terrain.elevation_at(position)
        if elevation is None:
            return None
        return self.chart_datum - elevation
