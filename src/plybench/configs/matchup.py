from __future__ import annotations

from dataclasses import dataclass

from plybench.configs.game_config import GameConfig
from plybench.configs.player_config import PlayerConfig


@dataclass(frozen=True, eq=True)
class Matchup:
    game: GameConfig
    i: PlayerConfig
    o: PlayerConfig
    num_games: int
