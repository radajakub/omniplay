from __future__ import annotations

from abc import ABC, abstractmethod

from omniplay.analysis.statistics.distribution import Distribution
from omniplay.common.enums import CIFamily, MetricName
from omniplay.configs.player_config import PlayerConfig
from omniplay.trackers.game_tracker import GameTracker


class Extractor(ABC):
    def __init__(self, name: MetricName, family: CIFamily) -> None:
        self.name = name
        self.family = family

    @abstractmethod
    def extract(self, games: list[GameTracker], player: PlayerConfig) -> Distribution:
        raise NotImplementedError
