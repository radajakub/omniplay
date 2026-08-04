from __future__ import annotations

from dataclasses import dataclass

from plybench.callbacks.benchmark_callbacks import BenchmarkCallbacks
from plybench.configs.game_config import GameConfig
from plybench.configs.player_config import PlayerConfig
from plybench.trackers.result_tracker import ResultTracker


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
