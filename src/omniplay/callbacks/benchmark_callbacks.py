from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from omniplay.harness.results import BenchmarkResults
from omniplay.configs.game_config import GameConfig
from omniplay.configs.player_config import PlayerConfig
from omniplay.trackers.result_tracker import ResultTracker

# Orchestration-layer phase hooks, the counterpart to the game-loop `GameCallbacks`. A caller (or an
# agent building a more complex evaluation flow) supplies these to observe/act at benchmark, matchup
# and round boundaries; they never drive gameplay. All slots are optional and null-guarded.
BenchmarkStartCallback = Callable[[list[str], list[str], list[str]], None]
BenchmarkEndCallback = Callable[['BenchmarkResults'], None]
MatchupStartCallback = Callable[['ResultTracker', 'GameConfig', 'PlayerConfig', 'PlayerConfig'], None]
MatchupEndCallback = Callable[['ResultTracker'], None]
RoundStartCallback = Callable[['GameConfig', 'PlayerConfig', 'PlayerConfig', int], None]
RoundCompleteCallback = Callable[['GameConfig', 'PlayerConfig', 'PlayerConfig', int], None]


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
        """Fan-out composite: every hook invokes each bundle's corresponding hook, in order. Lets a
        caller mix a console-progress bundle with an agent's own orchestration handlers."""
        children = tuple(bundle for bundle in bundles if bundle is not None)

        def fan(method_name: str) -> Callable[..., None]:
            def call(*args: object) -> None:
                for child in children:
                    getattr(child, method_name)(*args)
            return call

        return cls(
            benchmark_start_callback=fan('on_benchmark_start'),
            benchmark_end_callback=fan('on_benchmark_end'),
            matchup_start_callback=fan('on_matchup_start'),
            matchup_end_callback=fan('on_matchup_end'),
            round_start_callback=fan('on_round_start'),
            round_complete_callback=fan('on_round_complete'),
        )


def console_benchmark_callbacks() -> BenchmarkCallbacks:
    """Minimal default progress reporter built on the callbacks; prints one line per matchup boundary."""

    def on_matchup_start(result_tracker: ResultTracker, game_config: GameConfig, i: PlayerConfig, o: PlayerConfig) -> None:
        done = len(result_tracker.get_completed_games())
        print(f'[benchmark] {game_config.path}: {i.path} vs {o.path} ({done}/{result_tracker.n})')

    def on_matchup_end(result_tracker: ResultTracker) -> None:
        print(f'[benchmark] done: {result_tracker.game.path} {result_tracker.i.path} vs {result_tracker.o.path}')

    return BenchmarkCallbacks(matchup_start_callback=on_matchup_start, matchup_end_callback=on_matchup_end)
