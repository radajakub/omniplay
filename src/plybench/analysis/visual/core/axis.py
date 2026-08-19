from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from plybench.analysis.visual.core.layout import Bounds
from plybench.analysis.visual.core.ticks import TickSpec

Scale = Literal["linear", "log"]
Side = Literal["left", "right", "bottom", "top"]


@dataclass(frozen=True)
class Axis:
    label: str = ""
    limits: tuple[float, float] | None = None
    scale: Scale = "linear"
    ticks: TickSpec | None = None
    rotation: float = 0.0
    # (m, n): equal non-zero values select fixed scaling (always 10^m); (-n, n) is the only-when-needed mode
    sci: tuple[int, int] | None = None
    side: Side | None = None
    pad: float = 0.05
    include_zero: bool = False


def _padded(low: float, high: float, pad: float, scale: Scale) -> tuple[float, float]:
    if scale == "log":
        # padding a log axis additively would swallow the low decade whole
        factor = (high / low) ** pad if low > 0 and high > low else 1.0
        return (low / factor, high * factor)
    span = high - low
    margin = (abs(high) or 1.0) * pad if span == 0 else span * pad
    return (low - margin, high + margin)


def resolve_limits(axis: Axis, bounds: Bounds | None) -> tuple[float, float] | None:
    if axis.limits is not None:
        return axis.limits
    if bounds is None:
        return None
    low = min(bounds.low, 0.0) if axis.include_zero else bounds.low
    return _padded(low, max(bounds.high, low), axis.pad, axis.scale)
