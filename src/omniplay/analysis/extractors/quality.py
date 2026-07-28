from __future__ import annotations

from collections.abc import Callable

from omniplay.analysis.extractors.base import Extractor
from omniplay.analysis.replay import MemoizedReplay, build_replayer
from omniplay.analysis.statistics.distribution import Distribution
from omniplay.analysis.stats.step_stats import StepStats
from omniplay.common.enums import CIFamily, MetricName, StateClass
from omniplay.configs.game_config import GameConfig
from omniplay.configs.player_config import PlayerConfig
from omniplay.registry import Registry
from omniplay.trackers.game_tracker import GameTracker

ReplayFn = Callable[[GameTracker], list[StepStats]]


class OptimalityRateExtractor(Extractor):
    """Fraction of the analysed player's judged moves that were optimal. `non_trivial` restricts to
    genuine-choice (DECISION) states, where the optimal set is a strict subset of the legal moves."""

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
    """Mean regret (state value minus the value of the move actually played) over the player's moves."""

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
    """The optimality/regret extractors for a solvable game, sharing one memoized replay of the games."""
    replay = MemoizedReplay(build_replayer(registry, game_config), player_config)
    return [
        OptimalityRateExtractor(replay),
        OptimalityRateExtractor(replay, non_trivial=True),
        RegretExtractor(replay),
    ]
