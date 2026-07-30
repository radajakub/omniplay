from __future__ import annotations

from abc import ABC, abstractmethod

from plybench.analysis.statistics.distribution import Distribution
from plybench.common.enums import CIFamily, MetricName
from plybench.configs.player_config import PlayerConfig
from plybench.trackers.game_tracker import GameTracker


class Extractor(ABC):
    def __init__(self, name: MetricName, family: CIFamily) -> None:
        self.name = name
        self.family = family

    @abstractmethod
    def extract(self, games: list[GameTracker], player: PlayerConfig) -> Distribution:
        raise NotImplementedError
