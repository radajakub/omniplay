from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # rendering to files only; never depend on an interactive backend being present

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure as MplFigure  # noqa: E402

from plybench.analysis.visual.core.axis import Axis  # noqa: E402
from plybench.analysis.visual.core.axis_render import apply_axis  # noqa: E402
from plybench.analysis.visual.core.figure import Figure  # noqa: E402
from plybench.analysis.visual.core.layers.base import DrawContext  # noqa: E402
from plybench.analysis.visual.core.layout import Bounds  # noqa: E402
from plybench.analysis.visual.core.legend import LegendEntry, dedupe, draw_figure_legend, draw_panel_legend  # noqa: E402
from plybench.analysis.visual.core.panel import Panel  # noqa: E402
from plybench.analysis.visual.core.style import Style  # noqa: E402

# how far the axes area is pulled in to make room for a legend parked on the right
RIGHT_LEGEND_EDGE = 0.82


@dataclass(frozen=True)
class Placement:
    show_x_labels: bool
    show_y_labels: bool
    x_bounds: Bounds | None
    y_bounds: Bounds | None


def placements(spec: Figure) -> list[Placement]:
    bottom, start = spec.bottom_of_column(), spec.start_of_row()
    shared_x, shared_y = spec.shared_x_bounds(), spec.shared_y_bounds()
    return [
        Placement(
            show_x_labels=index in bottom,
            show_y_labels=not spec.share_y or index in start,
            x_bounds=shared_x if spec.share_x else panel.x_bounds(),
            y_bounds=shared_y if spec.share_y else panel.y_bounds(),
        )
        for index, panel in enumerate(spec.panels)
    ]


def build_figure(spec: Figure) -> MplFigure:
    if not spec.panels:
        raise ValueError("need at least one panel to build a figure")
    with plt.rc_context(spec.style.rc()):
        figure = plt.figure(figsize=spec.size())
        grid = figure.add_gridspec(spec.rows, spec.columns)
        entries: list[LegendEntry] = []

        for index, (panel, placement) in enumerate(zip(spec.panels, placements(spec), strict=True)):
            row, column = spec.cell(index)
            # add_subplot per panel rather than plt.subplots: this is the single thing that lets a
            # panel choose its own projection and sit next to a rectilinear one
            ax = figure.add_subplot(grid[row, column], projection=panel.projection)
            entries.extend(_draw_panel(ax, panel, spec, placement))

        if spec.legend is not None:
            draw_figure_legend(figure, dedupe(entries), spec.legend, spec.style)
        if spec.suptitle:
            figure.suptitle(spec.suptitle, color=spec.style.text_primary, fontsize=spec.style.title_size)
        figure.tight_layout(rect=_rect(spec))
    return figure


def render(spec: Figure, path: Path) -> Path:
    figure = build_figure(spec)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=spec.style.dpi, bbox_inches="tight")
    plt.close(figure)
    return path


def _rect(spec: Figure) -> tuple[float, float, float, float]:
    right_legend = (spec.legend is not None and spec.legend.placement == "right") or any(panel.legend is not None and panel.legend.placement == "right" for panel in spec.panels)
    return (0.0, 0.0, RIGHT_LEGEND_EDGE if right_legend else 1.0, 1.0)


def _draw_panel(ax: Axes, panel: Panel, spec: Figure, placement: Placement) -> list[LegendEntry]:
    palette = panel.palette if panel.palette is not None else spec.palette
    contexts = panel.contexts(spec.style, spec.panel_size, palette)

    _style_axes(ax, spec.style)
    for layer, ctx in zip(panel.layers, contexts, strict=True):
        layer.draw(ax, ctx)

    x_axis = spec.axis_x(panel)
    y_offset = apply_axis(ax, panel.y, "y", placement.y_bounds, spec.style)
    apply_axis(ax, x_axis, "x", placement.x_bounds, spec.style)
    _apply_labels(ax, panel, x_axis, spec.style, y_offset)

    if not placement.show_x_labels:
        ax.tick_params(axis="x", labelbottom=False)
        ax.set_xlabel("")
    if not placement.show_y_labels:
        ax.tick_params(axis="y", labelleft=False)
        ax.set_ylabel("")

    entries = _entries(panel, contexts)
    if panel.legend is not None:
        draw_panel_legend(ax, dedupe(entries), panel.legend, spec.style)
    return entries


def _entries(panel: Panel, contexts: list[DrawContext]) -> list[LegendEntry]:
    return [entry for layer, ctx in zip(panel.layers, contexts, strict=True) for entry in layer.legend_entries(ctx)]


def _apply_labels(ax: Axes, panel: Panel, x_axis: Axis, style: Style, y_offset: bool) -> None:
    ax.set_ylabel(panel.y.label, color=style.text_secondary)
    ax.set_xlabel(x_axis.label, color=style.text_secondary)
    if not panel.title:
        return
    # _update_title_position accounts for a top-positioned x axis but not for the y offset text, so a
    # visible scientific offset would otherwise collide with the title
    pad = style.font_size if y_offset else None
    ax.set_title(panel.title, color=style.text_primary, pad=pad)


def _style_axes(ax: Axes, style: Style) -> None:
    if style.grid:
        ax.grid(True, axis=style.grid_axis, color=style.grid_color, linewidth=style.grid_width, zorder=0)
        ax.set_axisbelow(True)
    # a non-rectilinear projection carries a different set of spines ("polar"), so each is checked
    for side, spine in ax.spines.items():
        spine.set_visible(side not in style.hide_spines)
        spine.set_color(style.grid_color)
    ax.tick_params(colors=style.text_secondary)
