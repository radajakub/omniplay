from __future__ import annotations

from omniplay.analysis.extractors.base import Extractor
from omniplay.analysis.statistics.distribution import Distribution
from omniplay.common.enums import CIFamily, GameResults, MetricName
from omniplay.configs.player_config import PlayerConfig
from omniplay.trackers.game_tracker import GameTracker

_SCORE = {
    GameResults.WIN: 1.0,
    GameResults.OPPONENT_FAIL: 1.0,
    GameResults.DRAW: 0.5,
    GameResults.LOSS: 0.0,
    GameResults.MY_FAIL: 0.0,
}


class ScoreExtractor(Extractor):
    def __init__(self) -> None:
        super().__init__(MetricName.SCORE, CIFamily.MEAN)

    def extract(self, games: list[GameTracker], player: PlayerConfig) -> Distribution:
        distribution = Distribution()
        for game in games:
            distribution.add(_SCORE[game.get_result(player)])
        return distribution
