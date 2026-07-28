"""Export a finished benchmark as a .tar.gz for the omniplay-website ingestion endpoint.

The archive contains experiment.json + results/benchmarks/ (raw games, with LLM traces flattened to the
website's schema) + analysis/benchmarks/ (per-matchup metrics and per-round game stats, incl.
optimality/regret for solvable games). Upload it to POST /ingestion.

Examples:
    uv run python scripts/export.py --experiment my_experiment --out my_experiment.tar.gz
    uv run python scripts/export.py --name commercial_ttt --games tic_tac_toe: \\
        --players llm:actions:text:openai:gpt-5.4:reasoning_effort=high --opponents optimal:stochastic=True \\
        --num-games 100 --out commercial_ttt.tar.gz
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import add_source_args, benchmark_from_args, build_op  # noqa: E402
from _website_export import build_archive  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_source_args(parser)
    parser.add_argument('--out', required=True, help='output .tar.gz path')
    parser.add_argument('--confidence', type=float, default=0.95, help='confidence level (default 0.95)')
    parser.add_argument('--include-fails', action='store_true', help='fold the player\'s own failed games into loss rate')
    args = parser.parse_args()

    op = build_op()
    benchmark = benchmark_from_args(op, args)
    # the archive wrapper dir (stripped by the website); use the experiment name
    counts = build_archive(op, benchmark, args.out, benchmark.experiment, confidence=args.confidence, include_fails=args.include_fails)

    print(f'wrote {args.out}: {counts["matchups"]} matchups, {counts["games"]} games, {counts["game_stats"]} game-stat files')


if __name__ == '__main__':
    main()
