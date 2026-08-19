from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Layout:
    width: float
    height: float


@dataclass(frozen=True)
class Bounds:
    low: float
    high: float
    value_low: float
    value_high: float

    @classmethod
    def of(cls, values: Sequence[float | None], intervals: Sequence[tuple[float, float] | None] | None = None) -> Bounds | None:
        present = [value for value in values if value is not None]
        if not present:
            return None
        edges = [edge for interval in (intervals or []) if interval is not None for edge in interval]
        return cls(min([*present, *edges]), max([*present, *edges]), min(present), max(present))

    @classmethod
    def at(cls, value: float) -> Bounds:
        return cls(value, value, value, value)

    def merge(self, other: Bounds) -> Bounds:
        return Bounds(
            min(self.low, other.low),
            max(self.high, other.high),
            min(self.value_low, other.value_low),
            max(self.value_high, other.value_high),
        )

    @classmethod
    def union(cls, items: Iterable[Bounds | None]) -> Bounds | None:
        merged: Bounds | None = None
        for item in items:
            if item is None:
                continue
            merged = item if merged is None else merged.merge(item)
        return merged
