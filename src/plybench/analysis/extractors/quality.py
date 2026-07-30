from __future__ import annotations

from collections.abc import Callable

from plybench.analysis.extractors.base import Extractor
from plybench.analysis.replay import MemoizedReplay, build_replayer
from plybench.analysis.statistics.distribution import Distribution
from plybench.analysis.stats.step_stats import StepStats
from plybench.common.enums import CIFamily, MetricName, StateClass
from plybench.configs.game_config import GameConfig
from plybench.configs.player_config import PlayerConfig
from plybench.registry import Registry
from plybench.trackers.game_tracker import GameTracker

ReplayFn = Callable[[GameTracker], list[StepStats]]


class OptimalityRateExtractor(Extractor):
    def __init__(self, replay: ReplayFn, non_trivial: bool = False) -> None:
        name = MetricName.OPTIMALITY_RATE_NON_TRIVIAL if non_trivial else MetricName.OPTIMALITY_RATE
        super().__init__(name, CIFamily.RATIO)
        self._replay = replay
        self._non_trivial = non_trivial

    def extract(self, games: list[GameTracker], player: PlayerConfig) -> Distribution:
        distribution = Distribution()
        for game in games:
            for step in self._replay(game):
                if self._non_trivial and step.state_class != StateClass.DECISION:
                    continue
                distribution.add(1.0 if step.is_optimal else 0.0)
        return distribution


class RegretExtractor(Extractor):
    def __init__(self, replay: ReplayFn) -> None:
        super().__init__(MetricName.REGRET, CIFamily.MEAN)
        self._replay = replay

    def extract(self, games: list[GameTracker], player: PlayerConfig) -> Distribution:
        distribution = Distribution()
        for game in games:
            for step in self._replay(game):
                distribution.add(step.regret)
        return distribution


def quality_extractors(registry: Registry, game_config: GameConfig, player_config: PlayerConfig) -> list[Extractor]:
    replay = MemoizedReplay(build_replayer(registry, game_config), player_config)
    return [
        OptimalityRateExtractor(replay),
        OptimalityRateExtractor(replay, non_trivial=True),
        RegretExtractor(replay),
    ]
