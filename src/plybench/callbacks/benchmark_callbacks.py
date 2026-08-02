from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from plybench.configs.game_config import GameConfig
from plybench.configs.player_config import PlayerConfig
from plybench.harness.results import BenchmarkResults
from plybench.trackers.result_tracker import ResultTracker

# Orchestration-layer phase hooks, the counterpart to the game-loop `GameCallbacks`. A caller (or an
# agent building a more complex evaluation flow) supplies these to observe/act at benchmark, matchup
# and round boundaries; they never drive gameplay. All slots are optional and null-guarded.
BenchmarkStartCallback = Callable[[list[str], list[str], list[str]], None]
BenchmarkEndCallback = Callable[["BenchmarkResults"], None]
MatchupStartCallback = Callable[["ResultTracker", "GameConfig", "PlayerConfig", "PlayerConfig"], None]
MatchupEndCallback = Callable[["ResultTracker"], None]
RoundStartCallback = Callable[["GameConfig", "PlayerConfig", "PlayerConfig", int], None]
RoundCompleteCallback = Callable[["GameConfig", "PlayerConfig", "PlayerConfig", int], None]


@dataclass
class BenchmarkCallbacks:
    benchmark_start_callback: BenchmarkStartCallback | None = None
    benchmark_end_callback: BenchmarkEndCallback | None = None
    matchup_start_callback: MatchupStartCallback | None = None
    matchup_end_callback: MatchupEndCallback | None = None
    round_start_callback: RoundStartCallback | None = None
    round_complete_callback: RoundCompleteCallback | None = None

    def on_benchmark_start(self, game_configs: list[str], player_configs: list[str], opponent_configs: list[str]) -> None:
        if self.benchmark_start_callback is not None:
            self.benchmark_start_callback(game_configs, player_configs, opponent_configs)

    def on_benchmark_end(self, results: BenchmarkResults) -> None:
        if self.benchmark_end_callback is not None:
            self.benchmark_end_callback(results)

    def on_matchup_start(self, result_tracker: ResultTracker, game_config: GameConfig, i: PlayerConfig, o: PlayerConfig) -> None:
        if self.matchup_start_callback is not None:
            self.matchup_start_callback(result_tracker, game_config, i, o)

    def on_matchup_end(self, result_tracker: ResultTracker) -> None:
        if self.matchup_end_callback is not None:
            self.matchup_end_callback(result_tracker)

    def on_round_start(self, game_config: GameConfig, i: PlayerConfig, o: PlayerConfig, game_round: int) -> None:
        if self.round_start_callback is not None:
            self.round_start_callback(game_config, i, o, game_round)

    def on_round_complete(self, game_config: GameConfig, i: PlayerConfig, o: PlayerConfig, game_round: int) -> None:
        if self.round_complete_callback is not None:
            self.round_complete_callback(game_config, i, o, game_round)

    @classmethod
    def combine(cls, *bundles: BenchmarkCallbacks | None) -> BenchmarkCallbacks:
        children = tuple(bundle for bundle in bundles if bundle is not None)

        def fan(method_name: str) -> Callable[..., None]:
            def call(*args: object) -> None:
                for child in children:
                    getattr(child, method_name)(*args)

            return call

        return cls(
            benchmark_start_callback=fan("on_benchmark_start"),
            benchmark_end_callback=fan("on_benchmark_end"),
            matchup_start_callback=fan("on_matchup_start"),
            matchup_end_callback=fan("on_matchup_end"),
            round_start_callback=fan("on_round_start"),
            round_complete_callback=fan("on_round_complete"),
        )


@dataclass
class _MatchupProgress:
    preexisting: set[int]
    n: int
    played: int = 0

    @property
    def done(self) -> int:
        return len(self.preexisting) + self.played


def console_benchmark_callbacks() -> BenchmarkCallbacks:
    # per-matchup state so round progress can show a running done/total and skip already-completed rounds on resume
    matchups: dict[tuple[str, str, str], _MatchupProgress] = {}

    def key(game_config: GameConfig, i: PlayerConfig, o: PlayerConfig) -> tuple[str, str, str]:
        return (game_config.path, i.path, o.path)

    def label(game_config: GameConfig, i: PlayerConfig, o: PlayerConfig) -> str:
        return f"{game_config.path}: {i.path} vs {o.path}"

    def on_matchup_start(result_tracker: ResultTracker, game_config: GameConfig, i: PlayerConfig, o: PlayerConfig) -> None:
        preexisting = set(result_tracker.get_completed_games())
        matchups[key(game_config, i, o)] = _MatchupProgress(preexisting, result_tracker.n)
        print(f"[benchmark] start {label(game_config, i, o)} ({len(preexisting)}/{result_tracker.n})")

    def on_round_complete(game_config: GameConfig, i: PlayerConfig, o: PlayerConfig, game_round: int) -> None:
        progress = matchups[key(game_config, i, o)]
        if game_round in progress.preexisting:  # already done before this run — don't log skipped rounds
            return
        progress.played += 1
        print(f"[benchmark] round {label(game_config, i, o)} — round {game_round} done ({progress.done}/{progress.n})")

    def on_matchup_end(result_tracker: ResultTracker) -> None:
        print(f"[benchmark] done {result_tracker.game.path}: {result_tracker.i.path} vs {result_tracker.o.path}")

    return BenchmarkCallbacks(
        matchup_start_callback=on_matchup_start,
        round_complete_callback=on_round_complete,
        matchup_end_callback=on_matchup_end,
    )
