from __future__ import annotations

from omniplay.analysis.stats.compute import compute_matchup_stats
from omniplay.analysis.stats.matchup_stats import MatchupStats
from omniplay.configs.game_config import GameConfig
from omniplay.configs.player_config import PlayerConfig
from omniplay.harness.results import BenchmarkResults
from omniplay.registry import Registry


class BenchmarkAnalysis:
    """In-memory statistical analysis over a finished benchmark: computes per-(player, opponent, game)
    matchup statistics (rates + score + moves + tokens, each with confidence intervals). When a
    `registry` is supplied, solvable games additionally get optimality/regret (via minimax replay).
    Nothing is persisted — the numbers are cheap to recompute from the recorded result files (the one
    expensive artefact, the solved minimax cache, is already cached on disk by the optimal judge)."""

    def __init__(self, results: BenchmarkResults, registry: Registry | None = None, confidence: float = 0.95, include_fails: bool = False) -> None:
        self.results = results
        self.registry = registry
        self.confidence = confidence
        self.include_fails = include_fails

    def matchup(self, game_config: GameConfig, player_config: PlayerConfig, opponent_config: PlayerConfig) -> MatchupStats:
        tracker = self.results.find(game_config, player_config, opponent_config)
        return compute_matchup_stats(tracker, self.registry, self.confidence, self.include_fails)

    def analyze(self) -> list[MatchupStats]:
        return [compute_matchup_stats(tracker, self.registry, self.confidence, self.include_fails) for tracker in self.results.trackers]
