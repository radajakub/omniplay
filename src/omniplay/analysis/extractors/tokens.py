from __future__ import annotations

from omniplay.analysis.extractors.base import Extractor
from omniplay.analysis.statistics.distribution import Distribution
from omniplay.common.enums import CIFamily, MetricName
from omniplay.configs.player_config import PlayerConfig
from omniplay.trackers.game_tracker import GameStep, GameTracker


def _player_steps(game: GameTracker, player: PlayerConfig, attr: str) -> list[GameStep]:
    # None tokens mean the player type has no token concept (a bot) -> excluded, not counted as 0
    return [step for step in game.steps if step.player_hash == player.hash and getattr(step, attr) is not None]


class TotalTokensExtractor(Extractor):
    """Total tokens the analysed player spent per game (summed over its moves)."""

    def __init__(self, name: MetricName, attr: str) -> None:
        super().__init__(name, CIFamily.MEAN)
        self._attr = attr

    def extract(self, games: list[GameTracker], player: PlayerConfig) -> Distribution:
        distribution = Distribution()
        for game in games:
            distribution.add(sum(getattr(step, self._attr) for step in _player_steps(game, player, self._attr)))
        return distribution


class PerMoveTokensExtractor(Extractor):
    """Tokens the analysed player spent on each individual move (one observation per move)."""

    def __init__(self, name: MetricName, attr: str) -> None:
        super().__init__(name, CIFamily.MEAN)
        self._attr = attr

    def extract(self, games: list[GameTracker], player: PlayerConfig) -> Distribution:
        distribution = Distribution()
        for game in games:
            for step in _player_steps(game, player, self._attr):
                distribution.add(getattr(step, self._attr))
        return distribution
