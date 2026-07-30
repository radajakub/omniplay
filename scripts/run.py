"""Run a benchmark: play every (player x opponent x game) matchup for `num_games` rounds and persist
the results under `results/benchmarks/` (resumable — already-completed rounds are skipped).

Examples:
    uv run python scripts/run.py --experiment my_experiment
    uv run python scripts/run.py --name smoke --games tic_tac_toe: --players random:distribution=uniform \\
        --opponents optimal:stochastic=True --num-games 10 --concurrency 4
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import add_source_args, benchmark_from_args, build_op  # noqa: E402

from plybench.callbacks.benchmark_callbacks import console_benchmark_callbacks  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_source_args(parser)
    parser.add_argument("--sync", action="store_true", help="run matchups sequentially instead of concurrently")
    parser.add_argument("--concurrency", type=int, help="max concurrent rounds per matchup (default: all missing)")
    args = parser.parse_args()

    op = build_op()
    benchmark = benchmark_from_args(op, args)

    results = asyncio.run(benchmark.run(sync=args.sync, concurrency=args.concurrency, benchmark_callbacks=console_benchmark_callbacks()))

    complete = sum(1 for tracker in results.trackers if tracker.is_complete())
    print(f"\ndone: {complete}/{len(results.trackers)} matchups complete under results/benchmarks/{benchmark.experiment}/")


if __name__ == "__main__":
    main()
