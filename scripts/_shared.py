"""Shared helpers for the repo-local scripts (not part of the installed package). Bootstraps a single
PlyBench object and resolves a Benchmark from either an experiment file or inline CLI arguments.

All scripts operate relative to the current working directory: benchmarks read/write
`experiments/benchmarks/` and `results/benchmarks/` under the cwd (the package's path convention)."""

from __future__ import annotations

import argparse

from plybench.app import PlyBench
from plybench.harness.benchmark import Benchmark
from plybench.llm import LLMConfig


def build_op() -> PlyBench:
    # from_env self-disables providers whose keys are absent, so bot-only scripts work offline too
    return PlyBench(LLMConfig.from_env())


def add_source_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--experiment", help="experiment name under experiments/benchmarks/<name>.json")
    parser.add_argument("--name", help="experiment name for an inline benchmark (and export wrapper)")
    parser.add_argument("--games", nargs="+", metavar="CONFIG", help="game config strings, e.g. tic_tac_toe:")
    parser.add_argument("--players", nargs="+", metavar="CONFIG", help="player config strings")
    parser.add_argument("--opponents", nargs="+", metavar="CONFIG", help="opponent config strings")
    parser.add_argument("--num-games", type=int, default=2, help="rounds per matchup (inline only; default 2)")


def benchmark_from_args(op: PlyBench, args: argparse.Namespace) -> Benchmark:
    if args.experiment:
        # per-axis overrides restrict the experiment's enabled set at run time
        return Benchmark.load_experiment(op, args.experiment, game_override=args.games, player_override=args.players, opponent_override=args.opponents)
    if not (args.games and args.players and args.opponents):
        raise SystemExit("provide --experiment, or all of --games / --players / --opponents (+ optional --num-games)")
    return Benchmark(args.name or "benchmark", op, args.games, args.players, args.opponents, args.num_games)
