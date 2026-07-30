from __future__ import annotations

from plybench.analysis.extractors.base import Extractor
from plybench.analysis.statistics.distribution import Distribution
from plybench.common.enums import CIFamily, GameResults, MetricName
from plybench.configs.player_config import PlayerConfig
from plybench.trackers.game_tracker import GameTracker


class OutcomeExtractor(Extractor):
    def __init__(self, name: MetricName, targets: list[GameResults]) -> None:
        super().__init__(name, CIFamily.RATIO)
        self._targets = targets

    def extract(self, games: list[GameTracker], player: PlayerConfig) -> Distribution:
        distribution = Distribution()
        for game in games:
            distribution.add(1.0 if game.get_result(player) in self._targets else 0.0)
        return distribution
