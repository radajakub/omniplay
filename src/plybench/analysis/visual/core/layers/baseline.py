from __future__ import annotations

from dataclasses import dataclass, field

from matplotlib.axes import Axes

from plybench.analysis.visual.core.layers.base import DrawContext
from plybench.analysis.visual.core.layout import Bounds
from plybench.analysis.visual.core.legend import LegendEntry
from plybench.analysis.visual.core.style import TEXT_SECONDARY, SeriesStyle, StyleOverride

DEFAULT = SeriesStyle(color=TEXT_SECONDARY, linestyle=(0, (4, 3)), marker="none", linewidth=1.0, alpha=0.9)


@dataclass(frozen=True)
class BaselineLayer:
    value: float
    label: str = ""
    annotate: bool = True
    in_legend: bool = False
    style: StyleOverride = field(default_factory=StyleOverride)

    @property
    def style_overrides(self) -> tuple[StyleOverride, ...]:
        return ()

    def bounds(self) -> Bounds | None:
        return Bounds.at(self.value)

    def x_bounds(self) -> Bounds | None:
        return None

    def legend_entries(self, ctx: DrawContext) -> list[LegendEntry]:
        return [LegendEntry(self.label, self.style.over(DEFAULT))] if self.label and self.in_legend else []

    def draw(self, ax: Axes, ctx: DrawContext) -> None:
        style = self.style.over(DEFAULT)
        ax.axhline(self.value, color=style.color, linestyle=style.linestyle, linewidth=style.linewidth, alpha=style.alpha, zorder=1)
        if self.label and self.annotate:
            below = self._sits_below(ctx)
            ax.annotate(
                self.label,
                xy=(0.995, self.value),
                xycoords=ax.get_yaxis_transform(),
                xytext=(0, -3 if below else 3),
                textcoords="offset points",
                ha="right",
                va="top" if below else "bottom",
                color=style.color,
                fontsize=ctx.style.font_size - 2,
            )

    def _sits_below(self, ctx: DrawContext) -> bool:
        peers = ctx.peer_bounds
        if peers is None:
            return False
        midpoint = (peers.value_low + peers.value_high) / 2
        return self.value < midpoint
