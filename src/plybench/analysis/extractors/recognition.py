from __future__ import annotations

from plybench.analysis.extractors.base import Extractor
from plybench.analysis.recognition import recognizable, step_reasoning_trace, trace_mentions_original_game
from plybench.analysis.statistics.distribution import Distribution
from plybench.common.enums import CIFamily, MetricName
from plybench.configs.player_config import PlayerConfig
from plybench.trackers.game_tracker import GameTracker


class RecognitionRateExtractor(Extractor):
    """Per-move proportion of the player's reasoning-bearing moves whose trace names the underlying game.
    Move-level (one 0/1 per reasoning trace); trace-less moves are excluded, not counted as misses."""

    def __init__(self, game_key: str) -> None:
        super().__init__(MetricName.RECOGNITION_RATE, CIFamily.RATIO)
        self._game_key = game_key

    def extract(self, games: list[GameTracker], player: PlayerConfig) -> Distribution:
        distribution = Distribution()
        for game in games:
            for step in game.steps:
                if step.player_hash != player.hash:
                    continue
                trace = step_reasoning_trace(step)
                if trace is None:
                    continue
                distribution.add(1.0 if trace_mentions_original_game(trace, self._game_key) else 0.0)
        return distribution


def recognition_extractors(game_key: str) -> list[Extractor]:
    # only defined for games built on a recognisable original; independent of solvability / a registry
    return [RecognitionRateExtractor(game_key)] if recognizable(game_key) else []
