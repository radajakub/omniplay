from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from omniplay.analysis.statistics.bundle import CIBundle
from omniplay.common.enums import MetricName
from omniplay.configs.game_config import GameConfig
from omniplay.configs.player_config import PlayerConfig

T = TypeVar('T')


@dataclass(frozen=True)
class Split(Generic[T]):
    """A value computed three ways over a matchup's games: all games, only those the analysed player
    started (i_first), and only those it played second (i_second) — to surface first-mover effects."""

    combined: T
    i_first: T
    i_second: T


@dataclass(frozen=True)
class MatchupMetrics:
    n_games: int
    metrics: dict[MetricName, CIBundle]

    def to_dict(self) -> dict[str, Any]:
        return {
            'n_games': self.n_games,
            'metrics': {name.value: bundle.to_dict() for name, bundle in self.metrics.items()},
        }


@dataclass(frozen=True)
class MatchupStats:
    experiment: str
    i: PlayerConfig
    o: PlayerConfig
    game: GameConfig
    n_games: int
    completed: list[int]
    metrics: Split[MatchupMetrics]

    def to_dict(self) -> dict[str, Any]:
        return {
            'experiment': self.experiment,
            'i_config': self.i.to_string(),
            'o_config': self.o.to_string(),
            'game_config': self.game.to_string(),
            'n_games': self.n_games,
            'completed': self.completed,
            'metrics': {
                'combined': self.metrics.combined.to_dict(),
                'i_first': self.metrics.i_first.to_dict(),
                'i_second': self.metrics.i_second.to_dict(),
            },
        }
