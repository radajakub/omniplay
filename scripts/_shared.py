"""Shared helpers for the repo-local scripts (not part of the installed package). Bootstraps a single
PlyBench object and resolves a Benchmark from either an experiment file or inline CLI arguments.

All scripts operate relative to the current working directory: benchmarks read/write
`experiments/benchmarks/` and `results/benchmarks/` under the cwd (the package's path convention)."""

from __future__ import annotations

import argparse
import json

from plybench.app import PlyBench
from plybench.common.paths import BenchmarkPathBuilder
from plybench.harness.benchmark import Benchmark
from plybench.harness.results import BenchmarkResults


def build_op(notif_enabled: bool = False, concurrency: int | None = None) -> PlyBench:
    # PlyBench's env config self-disables providers whose keys are absent, so bot-only scripts work offline too
    # notif_enabled is passed to the PlyBench constructor, which in turn passes it to the NotificationClient constructor
    # concurrency caps in-flight requests per provider -- the only limit that maps to an API rate quota
    return PlyBench(notif_enabled=notif_enabled, concurrency=concurrency)


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


def discover_matchups(op: PlyBench, experiment: str, game_str: str, paths: BenchmarkPathBuilder) -> tuple[set[str], set[str], int]:
    """Read every recorded matchup's metadata for one game to recover its exact model/opponent config
    strings and the games-per-matchup count, so nothing about the config space is hard-coded."""
    game = op.registry.game_config(game_str)
    models: set[str] = set()
    opponents: set[str] = set()
    num_games = 0
    for metadata in (paths.results_dir / experiment).glob(f"{game.path}_*/*/metadata.json"):
        data = json.loads(metadata.read_text())
        if data.get("game_config") != game.to_string():
            continue  # a different game whose path shares the prefix
        models.add(data["i_config"])
        opponents.add(data["o_config"])
        num_games = max(num_games, data.get("n_games", 0))
    return models, opponents, num_games


def load_paired_results(op: PlyBench, experiment: str, game_a: str, game_b: str, paths: BenchmarkPathBuilder) -> BenchmarkResults:
    """Load recorded results for two games over the models and opponents they have in common, which is
    what any A-vs-B comparison needs (a model present in only one game cannot be compared)."""
    models_a, opponents_a, n_a = discover_matchups(op, experiment, game_a, paths)
    models_b, opponents_b, n_b = discover_matchups(op, experiment, game_b, paths)
    models, opponents = sorted(models_a & models_b), sorted(opponents_a & opponents_b)
    if not models or not opponents:
        raise SystemExit("no shared models/opponents found for the two games (check --experiment and config strings)")
    return Benchmark(experiment, op, [game_a, game_b], models, opponents, max(n_a, n_b), paths).get_results()
