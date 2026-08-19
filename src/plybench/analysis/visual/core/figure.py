from __future__ import annotations

import math
from dataclasses import dataclass, field

from plybench.analysis.visual.core.axis import Axis
from plybench.analysis.visual.core.layout import Bounds, Layout
from plybench.analysis.visual.core.legend import LegendSpec
from plybench.analysis.visual.core.palette import Palette
from plybench.analysis.visual.core.panel import Panel
from plybench.analysis.visual.core.style import Style


@dataclass
class Figure:
    panels: list[Panel]
    ncols: int = 1
    panel_size: Layout = field(default_factory=lambda: Layout(7.0, 4.5))
    style: Style = field(default_factory=Style)
    x: Axis | None = None
    palette: Palette = field(default_factory=Palette)
    suptitle: str = ""
    legend: LegendSpec | None = field(default_factory=LegendSpec)
    share_x: bool = True
    share_y: bool = False

    @property
    def columns(self) -> int:
        return max(1, min(self.ncols, len(self.panels)))

    @property
    def rows(self) -> int:
        return math.ceil(len(self.panels) / self.columns)

    def cell(self, index: int) -> tuple[int, int]:
        return divmod(index, self.columns)

    def size(self) -> tuple[float, float]:
        return (self.panel_size.width * self.columns, self.panel_size.height * self.rows)

    def bottom_of_column(self) -> set[int]:
        lowest: dict[int, int] = {}
        for index in range(len(self.panels)):
            row, column = self.cell(index)
            if row >= lowest.get(column, -1):
                lowest[column] = row
        return {index for index in range(len(self.panels)) if self.cell(index)[0] == lowest[self.cell(index)[1]]}

    def start_of_row(self) -> set[int]:
        return {index for index in range(len(self.panels)) if self.cell(index)[1] == 0}

    def shared_y_bounds(self) -> Bounds | None:
        return Bounds.union(panel.y_bounds() for panel in self.panels) if self.share_y else None

    def shared_x_bounds(self) -> Bounds | None:
        return Bounds.union(panel.x_bounds() for panel in self.panels) if self.share_x else None

    def axis_x(self, panel: Panel) -> Axis:
        return panel.x if panel.x is not None else (self.x if self.x is not None else Axis())
