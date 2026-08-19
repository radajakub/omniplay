from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from matplotlib.axes import Axes

from plybench.analysis.visual.core.layout import Bounds, Layout
from plybench.analysis.visual.core.legend import LegendEntry
from plybench.analysis.visual.core.style import SeriesStyle, Style, StyleOverride


@dataclass(frozen=True)
class DrawContext:
    style: Style
    layout: Layout
    index: int
    styles: tuple[SeriesStyle, ...]
    peer_bounds: Bounds | None


@runtime_checkable
class Layer(Protocol):
    @property
    def style_overrides(self) -> tuple[StyleOverride, ...]: ...

    def bounds(self) -> Bounds | None: ...

    def x_bounds(self) -> Bounds | None: ...

    def legend_entries(self, ctx: DrawContext) -> list[LegendEntry]: ...

    def draw(self, ax: Axes, ctx: DrawContext) -> None: ...
