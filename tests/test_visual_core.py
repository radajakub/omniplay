"""The domain-free plotting core: how extents combine, how limits resolve, and who spends a palette
slot. None of this touches a benchmark, and only the smoke test touches a canvas."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pytest
from matplotlib.collections import PolyCollection

from plybench.analysis.visual import (
    Axis,
    BaselineLayer,
    Bounds,
    CategoryTicks,
    Figure,
    Layout,
    LegendSpec,
    LineLayer,
    Palette,
    Panel,
    SeriesStyle,
    StepTicks,
    Style,
    StyleOverride,
    build_figure,
    placements,
    resolve_limits,
)
from plybench.analysis.visual.core.axis_render import apply_axis
from plybench.analysis.visual.core.style import NEUTRAL


def line(*values: float | None, band: tuple[tuple[float, float] | None, ...] | None = None, color: str | None = None, label: str = "") -> LineLayer:
    return LineLayer(x=tuple(float(i) for i in range(len(values))), y=values, band=band, label=label, style=StyleOverride(color=color))


class TestBounds:
    def test_of_ignores_missing_values(self) -> None:
        assert Bounds.of((0.2, None, 0.8)) == Bounds(0.2, 0.8, 0.2, 0.8)

    def test_of_returns_none_when_nothing_is_present(self) -> None:
        assert Bounds.of((None, None)) is None

    def test_intervals_widen_the_limit_extent_but_not_the_value_extent(self) -> None:
        bounds = Bounds.of((0.5,), ((0.1, 0.9),))
        assert bounds == Bounds(0.1, 0.9, 0.5, 0.5)

    def test_union_skips_layers_that_contribute_nothing(self) -> None:
        assert Bounds.union([Bounds.at(1.0), None, Bounds.at(3.0)]) == Bounds(1.0, 3.0, 1.0, 3.0)


class TestResolveLimits:
    def test_explicit_limits_win_over_the_data(self) -> None:
        assert resolve_limits(Axis(limits=(0.0, 1.0)), Bounds(0.4, 0.6, 0.4, 0.6)) == (0.0, 1.0)

    def test_unconstrained_axis_defers_to_matplotlib(self) -> None:
        assert resolve_limits(Axis(), None) is None

    def test_padding_uses_the_error_extent_not_the_values(self) -> None:
        low, high = resolve_limits(Axis(pad=0.1), Bounds(0.0, 10.0, 4.0, 6.0)) or (0.0, 0.0)
        assert (low, high) == pytest.approx((-1.0, 11.0))

    def test_include_zero_extends_downwards_only(self) -> None:
        low, high = resolve_limits(Axis(pad=0.0, include_zero=True), Bounds(5.0, 10.0, 5.0, 10.0)) or (0.0, 0.0)
        assert (low, high) == pytest.approx((0.0, 10.0))

    def test_a_flat_series_still_gets_a_range(self) -> None:
        low, high = resolve_limits(Axis(pad=0.1), Bounds.at(4.0)) or (0.0, 0.0)
        assert low < 4.0 < high

    def test_log_padding_is_multiplicative(self) -> None:
        low, high = resolve_limits(Axis(scale="log", pad=0.5), Bounds(1.0, 100.0, 1.0, 100.0)) or (0.0, 0.0)
        assert (low, high) == pytest.approx((0.1, 1000.0))


class TestPaletteSlots:
    def test_slots_are_taken_from_the_front_in_order(self) -> None:
        panel = Panel(layers=[line(1.0), line(2.0)])
        first, second = panel.contexts(Style(), Layout(4.0, 3.0), Palette())
        assert (first.styles[0].color, second.styles[0].color) == (Palette().colors[0], Palette().colors[1])

    def test_a_decoration_layer_does_not_shift_the_series_after_it(self) -> None:
        panel = Panel(layers=[BaselineLayer(0.5), line(1.0)])
        _, curve = panel.contexts(Style(), Layout(4.0, 3.0), Palette())
        assert curve.styles[0].color == Palette().colors[0]

    def test_a_layer_naming_its_own_colour_spends_no_slot(self) -> None:
        panel = Panel(layers=[line(1.0, color="#123456"), line(2.0)])
        explicit, cycled = panel.contexts(Style(), Layout(4.0, 3.0), Palette())
        assert (explicit.styles[0].color, cycled.styles[0].color) == ("#123456", Palette().colors[0])

    def test_exhausting_the_palette_raises_rather_than_repeating_a_colour(self) -> None:
        panel = Panel(layers=[line(float(index)) for index in range(len(Palette().colors) + 1)])
        with pytest.raises(ValueError, match="exceeds the 8 available colours"):
            panel.contexts(Style(), Layout(4.0, 3.0), Palette())

    def test_overrides_are_merged_onto_the_slot_they_do_not_replace_it(self) -> None:
        panel = Panel(layers=[LineLayer(x=(0.0,), y=(1.0,), style=StyleOverride(linewidth=9.0))])
        (ctx,) = panel.contexts(Style(), Layout(4.0, 3.0), Palette())
        assert (ctx.styles[0].linewidth, ctx.styles[0].color) == (9.0, Palette().colors[0])


class TestPeerBounds:
    def test_a_layer_sees_every_other_layers_extent_but_not_its_own(self) -> None:
        panel = Panel(layers=[BaselineLayer(0.5), line(0.8, 0.9)])
        baseline, curve = panel.contexts(Style(), Layout(4.0, 3.0), Palette())
        assert baseline.peer_bounds == Bounds(0.8, 0.9, 0.8, 0.9)
        assert curve.peer_bounds == Bounds.at(0.5)

    def test_a_lone_layer_has_no_peers(self) -> None:
        (ctx,) = Panel(layers=[line(1.0)]).contexts(Style(), Layout(4.0, 3.0), Palette())
        assert ctx.peer_bounds is None


class TestStyleOverride:
    def test_unset_fields_leave_the_base_alone(self) -> None:
        base = SeriesStyle(color="#000000", linewidth=2.0)
        assert StyleOverride(color="#ffffff").over(base) == SeriesStyle(color="#ffffff", linewidth=2.0)

    def test_neutral_contributes_no_colour_of_its_own(self) -> None:
        assert StyleOverride(color="#abcdef").over(NEUTRAL).color == "#abcdef"


class TestLineLayer:
    def test_mismatched_lengths_are_rejected_at_construction(self) -> None:
        with pytest.raises(ValueError, match="2 x values for 3 y values"):
            LineLayer(x=(0.0, 1.0), y=(1.0, 2.0, 3.0))

    def test_a_gap_splits_the_band_into_separate_runs(self) -> None:
        layer = line(1.0, None, 3.0, band=((0.5, 1.5), None, (2.5, 3.5)))
        assert [[position for position, _ in run] for run in layer._runs()] == [[0.0], [2.0]]

    def test_bounds_span_the_band_and_the_values_separately(self) -> None:
        layer = line(1.0, 3.0, band=((0.5, 1.5), (2.5, 3.5)))
        assert layer.bounds() == Bounds(0.5, 3.5, 1.0, 3.0)

    def test_an_offset_moves_the_drawn_positions_and_the_x_extent_together(self) -> None:
        layer = LineLayer(x=(0.0, 1.0), y=(1.0, 2.0), x_offset=0.25)
        assert layer.positions() == (0.25, 1.25)
        assert layer.x_bounds() == Bounds(0.25, 1.25, 0.25, 1.25)

    def test_an_isolated_interval_is_drawn_as_a_whisker_because_a_fill_would_vanish(self) -> None:
        # a fill needs two positions to have any width, so a lone point's interval would be dropped
        figure = build_figure(Figure(panels=[Panel(layers=[line(0.5, band=((0.4, 0.6),))])], legend=None))
        ax = figure.axes[0]
        assert len(ax.containers) == 1  # the whisker
        assert [artist for artist in ax.collections if isinstance(artist, PolyCollection)] == []  # no fill
        plt.close(figure)

    def test_a_run_of_two_or_more_is_still_filled(self) -> None:
        figure = build_figure(Figure(panels=[Panel(layers=[line(0.5, 0.6, band=((0.4, 0.6), (0.5, 0.7)))])], legend=None))
        ax = figure.axes[0]
        assert ax.containers == []
        assert len([artist for artist in ax.collections if isinstance(artist, PolyCollection)]) == 1
        plt.close(figure)


class TestFigureGrid:
    def test_only_the_lowest_panel_in_each_column_keeps_its_x_labels(self) -> None:
        figure = Figure(panels=[Panel(layers=[line(1.0)]) for _ in range(5)], ncols=3)
        assert figure.bottom_of_column() == {2, 3, 4}

    def test_a_single_row_keeps_every_panels_labels(self) -> None:
        figure = Figure(panels=[Panel(layers=[line(1.0)]) for _ in range(3)], ncols=3)
        assert figure.bottom_of_column() == {0, 1, 2}


class TestSharedAxes:
    """A grid of one metric is read across its panels, so equal heights in two panels have to mean
    equal numbers. Without sharing they do not, and nothing about the figure says so."""

    @staticmethod
    def grid(share_y: bool) -> Figure:
        return Figure(panels=[Panel(layers=[line(0.0, 1.0)]), Panel(layers=[line(0.0, 10.0)])], ncols=2, share_y=share_y)

    def test_a_shared_y_scales_every_panel_to_the_widest_extent(self) -> None:
        first, second = placements(self.grid(share_y=True))
        assert first.y_bounds == second.y_bounds == Bounds(0.0, 10.0, 0.0, 10.0)

    def test_an_unshared_y_leaves_each_panel_on_its_own_extent(self) -> None:
        first, second = placements(self.grid(share_y=False))
        assert (first.y_bounds, second.y_bounds) == (Bounds.of((0.0, 1.0)), Bounds.of((0.0, 10.0)))

    def test_only_a_shared_y_may_drop_the_inner_panels_numbers(self) -> None:
        shared = placements(self.grid(share_y=True))
        assert [placement.show_y_labels for placement in shared] == [True, False]
        assert all(placement.show_y_labels for placement in placements(self.grid(share_y=False)))

    def test_the_shared_x_covers_every_panel_including_a_dodged_series(self) -> None:
        figure = Figure(panels=[Panel(layers=[LineLayer(x=(0.0,), y=(1.0,), x_offset=-0.3)]), Panel(layers=[LineLayer(x=(0.0,), y=(1.0,), x_offset=0.3)])], ncols=2)
        first, second = placements(figure)
        assert first.x_bounds == second.x_bounds == Bounds(-0.3, 0.3, -0.3, 0.3)


class TestSciNotation:
    """`scilimits` is two features behind one parameter, and whether an offset shows can only be
    learned after the locator has run. Both are easy to break and invisible until a figure is read."""

    @staticmethod
    def axis_of(sci: tuple[int, int], bounds: Bounds) -> tuple[bool, str]:
        figure = build_figure(Figure(panels=[Panel(layers=[line(bounds.low, bounds.high)], y=Axis(sci=sci))]))
        ax = figure.axes[0]
        showing = apply_axis(ax, Axis(sci=sci), "y", bounds, Style())
        return showing, ax.yaxis.get_offset_text().get_text()

    def test_symmetric_limits_only_offset_when_the_values_need_it(self) -> None:
        assert self.axis_of((-3, 3), Bounds(0.0, 1.0, 0.0, 1.0))[0] is False
        assert self.axis_of((-3, 3), Bounds(0.0, 5_000_000.0, 0.0, 5_000_000.0))[0] is True

    def test_equal_non_zero_limits_force_a_fixed_scale_even_on_a_small_axis(self) -> None:
        showing, text = self.axis_of((3, 3), Bounds(0.0, 1.0, 0.0, 1.0))
        assert showing is True
        assert "3" in text


class TestRender:
    def test_a_figure_of_mixed_layers_draws(self) -> None:
        panel = Panel(
            layers=[BaselineLayer(0.5, label="chance"), line(0.8, 0.6, 0.9, band=((0.7, 0.9), None, (0.85, 0.95)), label="model")],
            y=Axis(label="Rate", limits=(0.0, 1.0), ticks=StepTicks(0.2)),
            x=Axis(ticks=CategoryTicks(("a", "b", "c")), rotation=30.0),
            title="panel",
        )
        figure = build_figure(Figure(panels=[panel], suptitle="figure", legend=LegendSpec()))
        (ax,) = figure.axes[:1]
        assert [text.get_text() for text in ax.get_xticklabels()] == ["a", "b", "c"]
        assert ax.get_ylim() == (0.0, 1.0)
        assert [text.get_text() for text in figure.legends[0].get_texts()] == ["model"]

    def test_an_empty_figure_is_refused(self) -> None:
        with pytest.raises(ValueError, match="at least one panel"):
            build_figure(Figure(panels=[]))
