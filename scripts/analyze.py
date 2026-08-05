"""Compute and print benchmark statistics from persisted results (in memory; nothing is written).

Prints per-matchup metrics with confidence intervals. Solvable games also get optimality/regret unless
`--no-quality` is passed. `--partition` additionally splits each matchup's judged moves into groups and
compares every group against the baseline; no split is computed unless it is asked for.

Examples:
    uv run python scripts/analyze.py --experiment my_experiment
    uv run python scripts/analyze.py --experiment my_experiment --partition recognition sharpness
    uv run python scripts/analyze.py --name smoke --games tic_tac_toe: --players random:distribution=uniform \\
        --opponents optimal:stochastic=True --num-games 10
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import add_source_args, benchmark_from_args, build_op  # noqa: E402

from plybench.analysis import BenchmarkAnalysis  # noqa: E402
from plybench.analysis.statistics.bundle import CIBundle  # noqa: E402
from plybench.analysis.stats.matchup_stats import MatchupStats  # noqa: E402
from plybench.analysis.stats.move_features import UNGUARDED_FEATURES  # noqa: E402
from plybench.analysis.stats.move_metrics import DEFAULT_MOVE_METRICS  # noqa: E402
from plybench.analysis.stats.partition import PartitionStats, QuantilePartitioner  # noqa: E402

RECOGNITION = "recognition"
FEATURES = dict(UNGUARDED_FEATURES)


def _fmt(bundle: CIBundle, width: int = 10, interval: bool = True) -> str:
    if bundle.n == 0:  # no observations -> the value is undefined, not zero
        return f"{'NaN':>{width}s} (n=0)"
    ci = (bundle.wilson or bundle.t or bundle.sem or bundle.bootstrap) if interval else None
    bounds = f"  [{ci.lower:.4f}, {ci.upper:.4f}]" if ci is not None else ""
    return f"{bundle.value:{width}.4f}{bounds} (n={bundle.n})"


def _print_matchup(stats: MatchupStats) -> None:
    print(f"\n{stats.game.to_string()}  |  {stats.i.to_string()}  vs  {stats.o.to_string()}  |  n={stats.n_games}")
    for name, bundle in stats.metrics.combined.metrics.items():
        print(f"  {name.value:28s} {_fmt(bundle)}")


def _print_partition(stats: PartitionStats) -> None:
    print(f"\n{stats.game.to_string()}  |  {stats.i.to_string()}  vs  {stats.o.to_string()}  |  partition={stats.partitioner}  moves={stats.n_moves}")
    baseline = stats.groups[0].label
    header = f"  {'metric':28s}" + "".join(f" {f'{g.label} (n={g.n_moves})':>22s}" for g in stats.groups)
    header += "".join(f" {f'diff vs {baseline}':>18s} {'p':>8s}" for g in stats.groups[1:])
    print(header)
    for metric in DEFAULT_MOVE_METRICS:
        row = f"  {metric.name.value:28s}" + "".join(f" {_fmt(g.metrics[metric.name], width=8, interval=False):>22s}" for g in stats.groups)
        for g in stats.groups[1:]:
            comp = stats.comparisons[g.label][metric.name]
            diff = f"{comp.difference:+.4f}" if comp.difference is not None else "-"
            p = (f"{comp.p_value:.4f}" if comp.p_value is not None else "-") + ("*" if comp.significant else "")
            row += f" {diff:>18s} {p:>8s}"
        print(row)


def _split(analysis: BenchmarkAnalysis, name: str, bins: int) -> list[PartitionStats]:
    # recognition has its own guards (recognisable game, traces present); features are quantile-binned
    if name == RECOGNITION:
        return analysis.analyze_recognition()
    return analysis.analyze_partition(QuantilePartitioner(name, FEATURES[name], bins))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_source_args(parser)
    parser.add_argument("--confidence", type=float, default=0.95, help="confidence level (default 0.95)")
    parser.add_argument("--include-fails", action="store_true", help="fold the player's own failed games into loss rate")
    parser.add_argument("--no-quality", action="store_true", help="skip optimality/regret (no minimax replay)")
    parser.add_argument(
        "--partition", nargs="+", choices=[RECOGNITION, *FEATURES], metavar="NAME", help=f"move splits to compute: {', '.join([RECOGNITION, *FEATURES])} (default: none)"
    )
    parser.add_argument("--bins", type=int, default=3, help="quantile bins per feature partition (default 3)")
    args = parser.parse_args()

    if args.partition and args.no_quality:
        raise SystemExit("--partition needs the minimax replay; drop --no-quality")

    op = build_op()
    results = benchmark_from_args(op, args).get_results()
    registry = None if args.no_quality else op.registry
    analysis = BenchmarkAnalysis(results, registry, confidence=args.confidence, include_fails=args.include_fails)

    matchups = [stats for stats in analysis.analyze() if stats.completed]
    for stats in matchups:
        _print_matchup(stats)
    print(f"\n{len(matchups)} matchup(s) analyzed.")

    for name in args.partition or []:
        splits = _split(analysis, name, args.bins)
        print(f"\n=== {name} split ===")
        for split in splits:
            _print_partition(split)
        print(f"\n{len(splits)} matchup(s) split by {name}.")


if __name__ == "__main__":
    main()
