#!/usr/bin/env python3
# harbor_simulation/exceptions.py

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-22T18:40:30+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


class HarborSimulationBaseException(Exception):
    pass


class OutOfDomainError(HarborSimulationBaseException):
    pass


class InvalidBerthOperationError(HarborSimulationBaseException):
    pass


class InvalidVesselOperationError(HarborSimulationBaseException):
    pass


class InvalidMessagePayloadError(HarborSimulationBaseException):
    pass


class InvalidProjectionError(HarborSimulationBaseException):
    pass


class UnsupportedSpatialOperationError(HarborSimulationBaseException):
    pass


class InvalidTerrainGeometryError(HarborSimulationBaseException):
    pass


class AmbiguousTerrainElevationError(HarborSimulationBaseException):
    pass
