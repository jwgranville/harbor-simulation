#!/usr/bin/env python3
# tests/support.py

from harbor_simulation.quantitative import Distance, Position
from harbor_simulation.terrain import TerrainVertex

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-20T01:14:13+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


def terrain_vertex(x: int, y: int, elevation: float) -> TerrainVertex:
    return TerrainVertex(Position.from_components(x, y), Distance(elevation))
