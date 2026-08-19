"""Domain-free plotting core.

Three nested containers, each owning exactly one kind of decision: a Figure is a grid of panels plus
everything shared, a Panel is a list of layers and the axes they are drawn against, and a Layer is
one thing drawn, carrying its own data and its own styling. Nothing here knows what a benchmark, a
model or a metric is -- see `visual.bench` for that.
"""

from plybench.analysis.visual.core.axis import Axis, resolve_limits
from plybench.analysis.visual.core.figure import Figure
from plybench.analysis.visual.core.layers.base import DrawContext, Layer
from plybench.analysis.visual.core.layers.baseline import BaselineLayer
from plybench.analysis.visual.core.layers.line import LineLayer
from plybench.analysis.visual.core.layout import Bounds, Layout
from plybench.analysis.visual.core.legend import LegendEntry, LegendSpec
from plybench.analysis.visual.core.palette import CATEGORICAL, LINESTYLES, MARKERS, Palette
from plybench.analysis.visual.core.panel import Panel
from plybench.analysis.visual.core.render import Placement, build_figure, placements, render
from plybench.analysis.visual.core.style import GRID_COLOR, SURFACE, TEXT_PRIMARY, TEXT_SECONDARY, SeriesStyle, Style, StyleOverride
from plybench.analysis.visual.core.ticks import CategoryTicks, MaxTicks, StepTicks, TickSpec

__all__ = [
    "CATEGORICAL",
    "GRID_COLOR",
    "LINESTYLES",
    "MARKERS",
    "SURFACE",
    "TEXT_PRIMARY",
    "TEXT_SECONDARY",
    "Axis",
    "BaselineLayer",
    "Bounds",
    "CategoryTicks",
    "DrawContext",
    "Figure",
    "Layer",
    "Layout",
    "LegendEntry",
    "LegendSpec",
    "LineLayer",
    "MaxTicks",
    "Palette",
    "Panel",
    "Placement",
    "SeriesStyle",
    "StepTicks",
    "Style",
    "StyleOverride",
    "TickSpec",
    "build_figure",
    "placements",
    "render",
    "resolve_limits",
]
