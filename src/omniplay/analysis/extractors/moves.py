from __future__ import annotations

from omniplay.analysis.extractors.base import Extractor
from omniplay.analysis.statistics.distribution import Distribution
from omniplay.common.enums import CIFamily, MetricName
from omniplay.configs.player_config import PlayerConfig
from omniplay.trackers.game_tracker import GameTracker


class MovesPerGameExtractor(Extractor):
    """Number of moves the analysed player made in each game."""

    def __init__(self) -> None:
        super().__init__(MetricName.MOVES_PER_GAME, CIFamily.MEAN)

    def extract(self, games: list[GameTracker], player: PlayerConfig) -> Distribution:
        distribution = Distribution()
        for game in games:
            distribution.add(sum(1 for step in game.steps if step.player_hash == player.hash))
        return distribution
