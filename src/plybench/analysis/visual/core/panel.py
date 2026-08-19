from __future__ import annotations

from dataclasses import dataclass, field

from plybench.analysis.visual.core.axis import Axis
from plybench.analysis.visual.core.layers.base import DrawContext, Layer
from plybench.analysis.visual.core.layout import Bounds, Layout
from plybench.analysis.visual.core.legend import LegendSpec
from plybench.analysis.visual.core.palette import Palette
from plybench.analysis.visual.core.style import NEUTRAL, SeriesStyle, Style


@dataclass
class Panel:
    layers: list[Layer]
    y: Axis = field(default_factory=Axis)
    x: Axis | None = None
    title: str = ""
    projection: str | None = None
    palette: Palette | None = None
    legend: LegendSpec | None = None

    def y_bounds(self) -> Bounds | None:
        return Bounds.union(layer.bounds() for layer in self.layers)

    def x_bounds(self) -> Bounds | None:
        return Bounds.union(layer.x_bounds() for layer in self.layers)

    def contexts(self, style: Style, layout: Layout, palette: Palette) -> list[DrawContext]:
        bounds = [layer.bounds() for layer in self.layers]
        offsets = self._slot_offsets()
        return [
            DrawContext(
                style=style,
                layout=layout,
                index=index,
                styles=self._styles(layer, offsets[index], palette),
                peer_bounds=Bounds.union(other for position, other in enumerate(bounds) if position != index),
            )
            for index, layer in enumerate(self.layers)
        ]

    def _slot_offsets(self) -> list[int]:
        offsets: list[int] = []
        used = 0
        for layer in self.layers:
            offsets.append(used)
            used += _slots(layer)
        return offsets

    @staticmethod
    def _styles(layer: Layer, offset: int, palette: Palette) -> tuple[SeriesStyle, ...]:
        styles: list[SeriesStyle] = []
        used = offset
        for override in layer.style_overrides:
            if override.color is None:
                styles.append(override.over(palette.slot(used)))
                used += 1
            else:
                styles.append(override.over(NEUTRAL))
        return tuple(styles)


def _slots(layer: Layer) -> int:
    return sum(1 for override in layer.style_overrides if override.color is None)
