#!/usr/bin/env python3
# harbor_simulation/quantitative.py

import collections.abc
import dataclasses
import math
import numbers
import operator
import types

from harbor_simulation.exceptions import OutOfDomainError

__author__ = "Joe Granville"
__email__ = "874605+jwgranville@users.noreply.github.com"
__date__ = "2026-09-21T19:47:27+00:00"
__license__ = "MIT"
__version__ = "0.1.0.dev1"
__status__ = "Prototype"


type PartiallyImplemented[T] = T | types.NotImplementedType


@dataclasses.dataclass(frozen=True)
class NumericValue:
    value: numbers.Real


type NumericOperation = (
    collections.abc.Callable[[NumericValue, NumericValue], NumericValue]
)


@dataclasses.dataclass(frozen=True)
class Scalar(NumericValue):

    def __add__(self, other) -> PartiallyImplemented["Scalar"]:
        if isinstance(other, Scalar):
            return Scalar(self.value + other.value)
        return NotImplemented

    def __sub__(self, other) -> PartiallyImplemented["Scalar"]:
        if isinstance(other, Scalar):
            return Scalar(self.value - other.value)
        return NotImplemented

    def __mul__(self, other) -> PartiallyImplemented["Scalar | TimeDelta"]:
        if isinstance(other, TimeDelta):
            return TimeDelta(self.value * other.value)
        if isinstance(other, Scalar):
            return Scalar(self.value * other.value)
        return NotImplemented

    def __truediv__(self, other) -> PartiallyImplemented["Scalar"]:
        if isinstance(other, Scalar):
            return Scalar(self.value / other.value)
        return NotImplemented


@dataclasses.dataclass(frozen=True)
class Vector:
    components: tuple[NumericValue, ...]
    dimension: int = dataclasses.field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "dimension", len(self.components))

    def __len__(self) -> int:
        return len(self.components)

    def __iter__(self) -> collections.abc.Iterable[NumericValue]:
        return iter(self.components)

    def __getitem__(self, index) -> NumericValue:
        return self.components[index]

    def __add__(self, other) -> PartiallyImplemented["Vector"]:
        if isinstance(other, Vector):
            return _pairwise_operation(operator.add, self, other)
        return NotImplemented

    def __sub__(self, other) -> PartiallyImplemented["Vector"]:
        if isinstance(other, Vector):
            return _pairwise_operation(operator.sub, self, other)
        return NotImplemented

    def __mul__(self, other) -> PartiallyImplemented["Vector"]:
        if isinstance(other, NumericValue):
            return _elementwise_operation(operator.mul, self, other)
        return NotImplemented

    def __truediv__(self, other) -> PartiallyImplemented["Vector"]:
        if isinstance(other, NumericValue):
            return _elementwise_operation(operator.truediv, self, other)
        return NotImplemented


@dataclasses.dataclass(frozen=True)
class Time(NumericValue):

    def __lt__(self, other) -> PartiallyImplemented[bool]:
        if isinstance(other, Time):
            return self.value < other.value
        return NotImplemented

    def __le__(self, other) -> PartiallyImplemented[bool]:
        if isinstance(other, Time):
            return self.value <= other.value
        return NotImplemented

    def __add__(self, other) -> PartiallyImplemented["Time"]:
        if isinstance(other, TimeDelta):
            return Time(self.value + other.value)
        return NotImplemented

    def __sub__(self, other) -> PartiallyImplemented["Time | TimeDelta"]:
        if isinstance(other, TimeDelta):
            return Time(self.value - other.value)
        if isinstance(other, Time):
            return TimeDelta(self.value - other.value)
        return NotImplemented


@dataclasses.dataclass(frozen=True)
class TimeDelta(NumericValue):

    def __add__(self, other) -> PartiallyImplemented["TimeDelta"]:
        if isinstance(other, TimeDelta):
            return TimeDelta(self.value + other.value)
        return NotImplemented

    def __sub__(self, other) -> PartiallyImplemented["TimeDelta"]:
        if isinstance(other, TimeDelta):
            return TimeDelta(self.value - other.value)
        return NotImplemented

    def __mul__(self, other) -> PartiallyImplemented["TimeDelta"]:
        if isinstance(other, Scalar):
            return TimeDelta(self.value * other.value)
        return NotImplemented

    def __truediv__(self, other) -> PartiallyImplemented["Scalar | TimeDelta"]:
        if isinstance(other, Scalar):
            return TimeDelta(self.value / other.value)
        if isinstance(other, TimeDelta):
            return Scalar(self.value / other.value)
        return NotImplemented


@dataclasses.dataclass(frozen=True)
class TimeSpan:
    start: Time
    end: Time
    duration: TimeDelta = dataclasses.field(
        init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "duration", self.end - self.start)

    def __contains__(self, time: Time) -> bool:
        return self.start <= time <= self.end

    def __add__(self, other) -> PartiallyImplemented["TimeSpan"]:
        if isinstance(other, TimeDelta):
            return TimeSpan(self.start + other, self.end + other)
        return NotImplemented

    def __sub__(self, other) -> PartiallyImplemented["TimeSpan"]:
        if isinstance(other, TimeDelta):
            return TimeSpan(self.start - other, self.end - other)
        return NotImplemented

    def start_times_for(self, duration: TimeDelta) -> "TimeSpan | None":
        latest_start = self.end - duration
        if latest_start < self.start:
            return None
        return TimeSpan(self.start, latest_start)

    @classmethod
    def from_values(cls, start: numbers.Real, end: numbers.Real) -> "TimeSpan":
        return cls(Time(start), Time(end))


@dataclasses.dataclass(frozen=True)
class Distance(NumericValue):

    def __lt__(self, other) -> PartiallyImplemented[bool]:
        if isinstance(other, Distance):
            return self.value < other.value
        return NotImplemented

    def __le__(self, other) -> PartiallyImplemented[bool]:
        if isinstance(other, Distance):
            return self.value <= other.value
        return NotImplemented

    def __add__(self, other) -> PartiallyImplemented["Distance"]:
        if isinstance(other, Distance):
            return Distance(self.value + other.value)
        return NotImplemented

    def __sub__(self, other) -> PartiallyImplemented["Distance"]:
        if isinstance(other, Distance):
            return Distance(self.value - other.value)
        return NotImplemented

    def __mul__(self, other) -> PartiallyImplemented["Distance"]:
        if isinstance(other, Scalar):
            return Distance(self.value * other.value)
        return NotImplemented

    def __truediv__(
        self, other
    ) -> PartiallyImplemented["Distance | Scalar | Speed"]:
        if isinstance(other, Scalar):
            return Distance(self.value / other.value)
        if isinstance(other, Distance):
            return Scalar(self.value / other.value)
        if isinstance(other, TimeDelta):
            return Speed(self.value / other.value)
        return NotImplemented


@dataclasses.dataclass(frozen=True)
class Speed(NumericValue):

    def __mul__(self, other) -> PartiallyImplemented["Distance"]:
        if isinstance(other, TimeDelta):
            return Distance(self.value * other.value)
        return NotImplemented


@dataclasses.dataclass(frozen=True)
class Displacement:
    vector: Vector

    def __truediv__(self, other) -> PartiallyImplemented["Velocity"]:
        if isinstance(other, TimeDelta):
            return Velocity(self.vector / other)
        return NotImplemented

    def magnitude(self) -> Distance:
        components = (component.value for component in self.vector)
        return Distance(math.hypot(*components))

    @classmethod
    def from_components(cls, *components: numbers.Real) -> "Displacement":
        return cls(_vector_from_values(components, Distance))


@dataclasses.dataclass(frozen=True)
class Velocity:
    vector: Vector

    def __mul__(self, other) -> PartiallyImplemented["Displacement"]:
        if isinstance(other, TimeDelta):
            return Displacement(self.vector * other)
        return NotImplemented

    @classmethod
    def from_components(cls, *components: numbers.Real) -> "Velocity":
        return cls(_vector_from_values(components, Speed))


@dataclasses.dataclass(frozen=True)
class Point:
    coordinates: Vector

    def __add__(self, other) -> PartiallyImplemented["Point"]:
        if isinstance(other, Displacement):
            return Point(self.coordinates + other.vector)
        return NotImplemented

    def __sub__(self, other) -> PartiallyImplemented["Displacement | Point"]:
        if isinstance(other, Displacement):
            return Point(self.coordinates - other.vector)
        if isinstance(other, Point):
            return Displacement(self.coordinates - other.coordinates)
        return NotImplemented

    @classmethod
    def from_components(cls, *components: numbers.Real) -> "Point":
        return cls(_vector_from_values(components, Distance))


@dataclasses.dataclass(frozen=True)
class Position:
    point: Point

    def __add__(self, other) -> PartiallyImplemented["Position"]:
        if isinstance(other, Displacement):
            return Position(self.point + other)
        return NotImplemented

    def __sub__(self, other) -> PartiallyImplemented["Displacement"]:
        if isinstance(other, Position):
            return self.point - other.point
        return NotImplemented

    @classmethod
    def from_components(cls, *components: numbers.Real) -> "Position":
        return cls(Point.from_components(*components))


def planar_segment_parameter(
    position: Position, start: Position, end: Position
) -> Scalar | None:
    start_x, start_y = _planar_position_components(start)
    end_x, end_y = _planar_position_components(end)
    position_x, position_y = _planar_position_components(position)
    delta_x = end_x - start_x
    delta_y = end_y - start_y
    length_squared = delta_x * delta_x + delta_y * delta_y
    if math.isclose(length_squared, 0):
        raise OutOfDomainError

    offset_x = position_x - start_x
    offset_y = position_y - start_y
    determinant = offset_x * delta_y - offset_y * delta_x
    if not math.isclose(determinant, 0, abs_tol=1e-9):
        return None

    parameter = (offset_x * delta_x + offset_y * delta_y) / length_squared
    if parameter < 0 and not math.isclose(parameter, 0):
        return None
    if parameter > 1 and not math.isclose(parameter, 1):
        return None
    return Scalar(min(1.0, max(0.0, parameter)))


def planar_barycentric_weights(
    position: Position,
    vertices: tuple[Position, Position, Position],
) -> tuple[Scalar, Scalar, Scalar] | None:
    x, y = _planar_position_components(position)
    (x1, y1), (x2, y2), (x3, y3) = (
        _planar_position_components(vertex) for vertex in vertices
    )
    denominator = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
    if math.isclose(denominator, 0):
        raise OutOfDomainError

    first = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / denominator
    second = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / denominator
    third = 1 - first - second
    weights = (first, second, third)
    if any(weight < 0 and not math.isclose(weight, 0) for weight in weights):
        return None
    return tuple(Scalar(weight) for weight in weights)


def planar_convex_hull(
    positions: tuple[Position, ...],
) -> tuple[Position, ...]:
    positions_by_coordinates = {
        _planar_position_components(position): position
        for position in positions
    }
    ordered = sorted(positions_by_coordinates.items())
    if len(ordered) <= 1:
        return tuple(position for _, position in ordered)

    lower: list[tuple[tuple[numbers.Real, numbers.Real], Position]] = []
    for coordinates, position in ordered:
        while (
            len(lower) >= 2
            and _turn_determinant(lower[-2][0], lower[-1][0], coordinates) <= 0
        ):
            lower.pop()
        lower.append((coordinates, position))

    upper: list[tuple[tuple[numbers.Real, numbers.Real], Position]] = []
    for coordinates, position in reversed(ordered):
        while (
            len(upper) >= 2
            and _turn_determinant(upper[-2][0], upper[-1][0], coordinates) <= 0
        ):
            upper.pop()
        upper.append((coordinates, position))

    hull = lower[:-1] + upper[:-1]
    return tuple(position for _, position in hull)


def _planar_position_components(
    position: Position,
) -> tuple[numbers.Real, numbers.Real]:
    coordinates = tuple(
        component.value for component in position.point.coordinates
    )
    if len(coordinates) != 2:
        raise OutOfDomainError
    return coordinates[0], coordinates[1]


def _turn_determinant(
    origin: tuple[numbers.Real, numbers.Real],
    first: tuple[numbers.Real, numbers.Real],
    second: tuple[numbers.Real, numbers.Real],
) -> numbers.Real:
    first_x = first[0] - origin[0]
    first_y = first[1] - origin[1]
    second_x = second[0] - origin[0]
    second_y = second[1] - origin[1]
    return first_x * second_y - first_y * second_x


def _counterclockwise_polygon(
    positions: tuple[Position, ...],
) -> tuple[Position, ...]:
    area = 0
    for start, end in _polygon_edges(positions):
        start_x, start_y = _planar_position_components(start)
        end_x, end_y = _planar_position_components(end)
        area += start_x * end_y - end_x * start_y
    if area < 0:
        return tuple(reversed(positions))
    return positions


def _polygon_edges(
    positions: tuple[Position, ...],
) -> tuple[tuple[Position, Position], ...]:
    return tuple(zip(positions, positions[1:] + positions[:1], strict=True))


def _clip_polygon(
    positions: tuple[Position, ...], start: Position, end: Position
) -> tuple[Position, ...]:
    if not positions:
        return ()

    clipped = []
    previous = positions[-1]
    previous_inside = _position_on_left(previous, start, end)
    for position in positions:
        inside = _position_on_left(position, start, end)
        if inside and not previous_inside:
            clipped.append(_line_intersection(previous, position, start, end))
        if inside:
            clipped.append(position)
        elif previous_inside:
            clipped.append(_line_intersection(previous, position, start, end))
        previous = position
        previous_inside = inside
    return tuple(clipped)


def _position_on_left(
    position: Position, start: Position, end: Position
) -> bool:
    start_coordinates = _planar_position_components(start)
    end_coordinates = _planar_position_components(end)
    position_coordinates = _planar_position_components(position)
    determinant = _turn_determinant(
        start_coordinates, end_coordinates, position_coordinates
    )
    return determinant > 0 or math.isclose(determinant, 0, abs_tol=1e-9)


def _line_intersection(
    first_start: Position,
    first_end: Position,
    second_start: Position,
    second_end: Position,
) -> Position:
    first_x, first_y = _planar_position_components(first_start)
    first_end_x, first_end_y = _planar_position_components(first_end)
    second_x, second_y = _planar_position_components(second_start)
    second_end_x, second_end_y = _planar_position_components(second_end)
    first_delta_x = first_end_x - first_x
    first_delta_y = first_end_y - first_y
    second_delta_x = second_end_x - second_x
    second_delta_y = second_end_y - second_y
    denominator = (
        first_delta_x * second_delta_y - first_delta_y * second_delta_x
    )
    if math.isclose(denominator, 0, abs_tol=1e-9):
        raise OutOfDomainError

    offset_x = second_x - first_x
    offset_y = second_y - first_y
    parameter = (
        offset_x * second_delta_y - offset_y * second_delta_x
    ) / denominator
    position = Position.from_components(
        first_x + parameter * first_delta_x,
        first_y + parameter * first_delta_y,
    )
    return position


def planar_convex_polygon_intersection(
    subject: tuple[Position, ...], clip: tuple[Position, ...]
) -> tuple[Position, ...]:
    intersection = _counterclockwise_polygon(subject)
    clip = _counterclockwise_polygon(clip)
    for start, end in _polygon_edges(clip):
        intersection = _clip_polygon(intersection, start, end)
        if not intersection:
            break
    return tuple(intersection)


def _pairwise_operation(
    operation: NumericOperation, left: Vector, right: Vector
) -> Vector:
    pairs = zip(left.components, right.components, strict=True)
    components = tuple(operation(left, right) for left, right in pairs)
    return Vector(components)


def _elementwise_operation(
    operation: NumericOperation, vector: Vector, scalar: NumericValue
) -> Vector:
    components = tuple(
        operation(component, scalar) for component in vector.components
    )
    return Vector(components)


def _vector_from_values(
    values: collections.abc.Iterable[numbers.Real],
    *value_types: type[NumericValue],
) -> Vector:
    values = tuple(values)

    if len(value_types) == 1:
        value_type = value_types[0]
        components = tuple(value_type(value) for value in values)
        return Vector(components)

    pairs = zip(value_types, values, strict=True)
    components = tuple(value_type(value) for value_type, value in pairs)
    return Vector(components)
