from __future__ import annotations

from plybench.analysis.extractors.base import Extractor
from plybench.analysis.statistics.distribution import Distribution
from plybench.common.enums import CIFamily, MetricName
from plybench.configs.player_config import PlayerConfig
from plybench.trackers.game_tracker import GameTracker


class MovesPerGameExtractor(Extractor):
    def __init__(self) -> None:
        super().__init__(MetricName.MOVES_PER_GAME, CIFamily.MEAN)

    def extract(self, games: list[GameTracker], player: PlayerConfig) -> Distribution:
        distribution = Distribution()
        for game in games:
            distribution.add(sum(1 for step in game.steps if step.player_hash == player.hash))
        return distribution
