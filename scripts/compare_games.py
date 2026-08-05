"""Compare two games move-for-move, per model and per opponent (nothing is written).

For every LLM model and every opponent the two games share, tests the difference (game A minus game B)
on optimality-rate (non-trivial), regret and output-tokens-per-move, with the family-appropriate test
(two-proportion z / Welch's t). Then summarises across opponents by averaging the per-opponent
differences (opponents are never pooled at the move level) with a combined-SE z-test.

Built generically for any pair of games; intended mainly for magic-square add=0 vs add=5.

Example:
    uv run python scripts/compare_games.py \\
        --game-a "magic_square:sample=False,magic_constant_add=0" \\
        --game-b "magic_square:sample=False,magic_constant_add=5"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import build_op, load_paired_results  # noqa: E402

from plybench.analysis.stats.move_metrics import DEFAULT_MOVE_METRICS  # noqa: E402
from plybench.analysis.studies.cross_game import AverageDiff, CellDiff, MetricDiff, ModelDiff, compare_games  # noqa: E402
from plybench.common.enums import MetricName  # noqa: E402
from plybench.common.paths import BenchmarkPathBuilder  # noqa: E402

PATHS = BenchmarkPathBuilder()

REPORTED_METRICS: tuple[MetricName, ...] = (
    MetricName.OPTIMALITY_RATE_NON_TRIVIAL,
    MetricName.REGRET,
    MetricName.OUTPUT_TOKENS_PER_MOVE,
)
SHORT_METRIC: dict[MetricName, str] = {
    MetricName.OPTIMALITY_RATE_NON_TRIVIAL: "optimality_nt",
    MetricName.REGRET: "regret",
    MetricName.OUTPUT_TOKENS_PER_MOVE: "out_tokens/move",
}


def _model_label(config) -> str:
    return config.to_string().removeprefix("llm:actions:text:")


def _fmt_p(p: float | None, significant: bool) -> str:
    if p is None:
        return f"{'-':>9s}"
    return f"{p:9.4f}" + ("*" if significant else " ")


def _fmt_diff(diff: MetricDiff) -> str:
    comp = diff.comparison
    d = f"{comp.difference:+9.4f}" if comp.difference is not None else f"{'-':>9s}"
    return f"{diff.value_a:10.4f} {diff.value_b:10.4f} {d} {_fmt_p(comp.p_value, comp.significant)}"


def _fmt_avg(avg: AverageDiff) -> str:
    d = f"{avg.mean_difference:+9.4f}" if avg.mean_difference is not None else f"{'-':>9s}"
    se = f"{avg.se:9.4f}" if avg.se is not None else f"{'-':>9s}"
    return f"{d} {se} {_fmt_p(avg.p_value, avg.significant)}  (k={avg.k})"


def _print_cell(cell: CellDiff) -> None:
    print(f"    opponent: {cell.opponent.to_string()}   (moves: A={cell.n_moves_a}, B={cell.n_moves_b})")
    print(f"      {'metric':16s} {'A':>10s} {'B':>10s} {'diff(A-B)':>9s} {'p':>9s}")
    for name in REPORTED_METRICS:
        print(f"      {SHORT_METRIC[name]:16s} {_fmt_diff(cell.metrics[name])}")


def _print_average(model: ModelDiff) -> None:
    print(f"    AVERAGE across {len(model.per_opponent)} opponents (per-opponent diffs, not pooled)")
    print(f"      {'metric':16s} {'mean diff':>9s} {'se':>9s} {'p':>9s}")
    for name in REPORTED_METRICS:
        print(f"      {SHORT_METRIC[name]:16s} {_fmt_avg(model.average[name])}")


def _print_model(model: ModelDiff) -> None:
    print(f"\n=== {_model_label(model.model)} ===")
    for cell in model.per_opponent:
        _print_cell(cell)
    _print_average(model)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--experiment", default="ttt", help="experiment name under results/benchmarks/ (default ttt)")
    parser.add_argument("--game-a", required=True, help="first game config string (differences are A minus B)")
    parser.add_argument("--game-b", required=True, help="second game config string")
    parser.add_argument("--confidence", type=float, default=0.95, help="confidence level (default 0.95)")
    args = parser.parse_args()

    op = build_op()
    results = load_paired_results(op, args.experiment, args.game_a, args.game_b, PATHS)
    diffs = compare_games(results, op.registry, args.game_a, args.game_b, DEFAULT_MOVE_METRICS, args.confidence)

    print(f"Comparing A={args.game_a}  vs  B={args.game_b}")
    print(f"differences are A minus B; * marks p < {1 - args.confidence:.2g}")
    for model in diffs:
        _print_model(model)
    print(f"\n{len(diffs)} model(s) compared.")


if __name__ == "__main__":
    main()
