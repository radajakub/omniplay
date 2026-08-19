from __future__ import annotations

from dataclasses import dataclass, field

from plybench.analysis.statistics.bundle import CIBundle
from plybench.analysis.visual.bench.encoder import StyleEncoder
from plybench.analysis.visual.bench.labels import Overrides, game_labels, metric_label
from plybench.analysis.visual.bench.series import Series
from plybench.analysis.visual.core.axis import Axis
from plybench.analysis.visual.core.layers.base import Layer
from plybench.analysis.visual.core.layers.line import LineLayer
from plybench.analysis.visual.core.panel import Panel
from plybench.analysis.visual.core.style import StyleOverride
from plybench.analysis.visual.core.ticks import CategoryTicks, StepTicks
from plybench.common.enums import MetricName

# a rate axis is fixed to its full range and stepped explicitly; nothing about a proportion should be
# inferred from the values that happen to have been observed
RATE_STEP = 0.2

# how much of the single category the series are spread across when there is nothing to connect
SINGLE_CATEGORY_SPREAD = 0.6


@dataclass(frozen=True)
class LineOptions:
    show_ci: bool = True
    # markers carry the reasoning effort, so dropping them merges a model's efforts into one line
    show_markers: bool = True
    ci_alpha: float = 0.12
    # thin: a dozen overlapping series on one panel is the normal case here, and heavy strokes hide
    # both each other and the confidence bands underneath them
    linewidth: float = 1.2
    marker_size: float = 4.0
    ylim: tuple[float, float] | None = None
    tick_rotation: float = 0.0
    label_overrides: Overrides = field(default_factory=dict)


def interval_of(bundle: CIBundle) -> tuple[float, float] | None:
    interval = bundle.wilson or bundle.t or bundle.sem or bundle.bootstrap
    return (interval.lower, interval.upper) if interval is not None else None


def is_ratio(series: list[Series]) -> bool:
    # a Wilson interval is only ever attached to a proportion, so it identifies the family without
    # having to re-derive it from the extractor that produced the bundle
    return any(point.bundle.wilson is not None for item in series for point in item.points if point.bundle is not None)


def dodges(count: int, categories: int) -> list[float]:
    if categories > 1 or count < 2:
        return [0.0] * count
    step = SINGLE_CATEGORY_SPREAD / (count - 1)
    return [index * step - SINGLE_CATEGORY_SPREAD / 2 for index in range(count)]


def series_layer(item: Series, encoder: StyleEncoder, options: LineOptions, x_offset: float = 0.0) -> LineLayer:
    resolved = encoder.style(item.style)
    return LineLayer(
        x=tuple(float(position) for position in range(len(item.points))),
        y=tuple(point.bundle.value if point.bundle is not None else None for point in item.points),
        label=item.label,
        band=tuple(interval_of(point.bundle) if point.bundle is not None else None for point in item.points) if options.show_ci else None,
        show_markers=options.show_markers,
        x_offset=x_offset,
        style=StyleOverride(
            color=resolved.color,
            linestyle=resolved.linestyle,
            marker=resolved.marker,
            linewidth=options.linewidth,
            markersize=options.marker_size,
            fill_alpha=options.ci_alpha,
        ),
    )


def metric_axis(series: list[Series], metric: MetricName, options: LineOptions) -> Axis:
    label = metric_label(metric.value)
    if options.ylim is not None:
        return Axis(label=label, limits=options.ylim)
    if is_ratio(series):
        return Axis(label=label, limits=(0.0, 1.0), ticks=StepTicks(RATE_STEP))
    return Axis(label=label)


def games_axis(series: list[Series], options: LineOptions) -> Axis:
    games = [point.game for point in series[0].points]
    return Axis(ticks=CategoryTicks(tuple(game_labels(games, options.label_overrides or None))), rotation=options.tick_rotation)


def metric_panel(series: list[Series], metric: MetricName, encoder: StyleEncoder, options: LineOptions | None = None, title: str = "") -> Panel:
    if not series:
        raise ValueError("a metric panel needs at least one series")
    counts = {len(item.points) for item in series}
    if len(counts) > 1:
        raise ValueError(f"series cover different numbers of games ({sorted(counts)}); one x position would mean a different game per line")
    options = options or LineOptions()
    offsets = dodges(len(series), counts.pop())
    layers: list[Layer] = [series_layer(item, encoder, options, offset) for item, offset in zip(series, offsets, strict=True)]
    return Panel(layers=layers, y=metric_axis(series, metric, options), x=games_axis(series, options), title=title)
