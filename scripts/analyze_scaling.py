"""Token-scaling / difficulty analysis on two games, per model (nothing is written).

Restricts to genuine decision points, then per LLM model:
  1. within game A: does token spend slope up with tactical sharpness, and does spending more buy
     accuracy within a fixed difficulty bin (the reasoner-vs-retriever test)?
  2. across games (A vs B): how does the token<-sharpness slope shift (read the slope, not the
     intercept, which absorbs add=5's arithmetic cost)?

Built generically for any pair of games; intended mainly for magic-square add=0 (A) vs add=5 (B).

Example:
    uv run python scripts/analyze_scaling.py \\
        --game-a "magic_square:sample=False,magic_constant_add=0" \\
        --game-b "magic_square:sample=False,magic_constant_add=5"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import build_op, load_paired_results  # noqa: E402

from plybench.analysis.statistics.regression import FitDifference, LinearFit  # noqa: E402
from plybench.analysis.studies.scaling import AccuracySpend, ModelScaling, analyze_scaling  # noqa: E402
from plybench.common.paths import BenchmarkPathBuilder  # noqa: E402

PATHS = BenchmarkPathBuilder()


def _model_label(config) -> str:
    return config.to_string().removeprefix("llm:actions:text:")


def _star(significant: bool) -> str:
    return "*" if significant else " "


def _fmt_slope(fit: LinearFit) -> str:
    if fit.slope is None:
        return f"{'-':>10s} {'':>10s} {'':>9s}  (n={fit.n})"
    p = f"{fit.p_value:.4f}{_star(fit.p_value is not None and fit.p_value < 0.05)}"
    return f"{fit.slope:+10.2f} {f'r={fit.r:+.3f}':>10s} {p:>10s}  (n={fit.n})"


def _fmt_shift(shift: FitDifference) -> str:
    if shift.delta_slope is None:
        return f"slope_A={_num(shift.slope_a)} slope_B={_num(shift.slope_b)}  (delta undefined)"
    p = f"{shift.p_value:.4f}{_star(shift.significant)}" if shift.p_value is not None else "-"
    intercept = f"  d_intercept={shift.delta_intercept:+.1f}" if shift.delta_intercept is not None else ""
    return f"slope_A={shift.slope_a:+.2f} slope_B={shift.slope_b:+.2f}  d_slope={shift.delta_slope:+8.2f}  p={p:>9s}{intercept}"


def _num(value: float | None) -> str:
    return f"{value:+.2f}" if value is not None else "-"


def _print_within(scaling: ModelScaling) -> None:
    print(f"  [within A] token<-feature OLS slopes  (decision moves, n={scaling.n_a})")
    for label, slope in scaling.within.items():
        print(f"    {label:12s} slope/unit: {_fmt_slope(slope)}")


def _print_spend(spend: AccuracySpend) -> None:
    print("  [within A] accuracy buys spend?  optimal-minus-suboptimal token spend, per sharpness bin")
    for b in spend.bins:
        diff = b.comparison.difference
        cell = f"{diff:+9.1f}" if diff is not None else f"{'-':>9s}"
        p = f"{b.comparison.p_value:.4f}{_star(b.comparison.significant)}" if b.comparison.p_value is not None else "-"
        print(f"    {b.label:22s} d_tokens={cell}  p={p:>9s}  (opt={b.n_optimal}, sub={b.n_suboptimal})")
    c = spend.combined
    if c.value is None:
        print("    combined across bins: undefined (no bin had both optimal and suboptimal moves)")
    else:
        p = f"{c.p_value:.4f}{_star(c.significant)}" if c.p_value is not None else "-"
        print(f"    combined across bins: d_tokens={c.value:+9.1f}  se={c.se:.1f}  p={p:>9s}  (k={c.k})")


def _print_shift(scaling: ModelScaling) -> None:
    if not scaling.shifts:
        print("  [A vs B] slope shift: unavailable (no decision moves in B)")
        return
    print(f"  [A vs B] token<-feature slope shift (A minus B, n_B={scaling.n_b})")
    for label, shift in scaling.shifts.items():
        print(f"    {label:12s} {_fmt_shift(shift)}")


def _print_model(scaling: ModelScaling) -> None:
    print(f"\n=== {_model_label(scaling.model)} ===")
    _print_within(scaling)
    _print_spend(scaling.accuracy_spend)
    _print_shift(scaling)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--experiment", default="ttt", help="experiment name under results/benchmarks/ (default ttt)")
    parser.add_argument("--game-a", required=True, help="within-game analysis runs on this game; shifts are A minus B")
    parser.add_argument("--game-b", required=True, help="second game, for the cross-game slope shift")
    parser.add_argument("--bins", type=int, default=3, help="number of sharpness quantile bins (default 3)")
    parser.add_argument("--confidence", type=float, default=0.95, help="confidence level (default 0.95)")
    args = parser.parse_args()

    op = build_op()
    results = load_paired_results(op, args.experiment, args.game_a, args.game_b, PATHS)
    scalings = analyze_scaling(results, op.registry, args.game_a, args.game_b, n_bins=args.bins, confidence=args.confidence)

    print(f"A={args.game_a}  B={args.game_b}")
    print(f"sharpness = 1 - #optimal/#legal (higher = harder); * marks p < {1 - args.confidence:.2g}")
    for scaling in scalings:
        _print_model(scaling)
    print(f"\n{len(scalings)} model(s) analysed.")


if __name__ == "__main__":
    main()
