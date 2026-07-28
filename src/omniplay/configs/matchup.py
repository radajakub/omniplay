from __future__ import annotations

from dataclasses import dataclass

from omniplay.configs.game_config import GameConfig
from omniplay.configs.player_config import PlayerConfig


@dataclass(frozen=True, eq=True)
class Matchup:
    """A single matchup to run: two players (i, o) on one game, played `num_games` colour-balanced rounds."""

    game: GameConfig
    i: PlayerConfig
    o: PlayerConfig
    num_games: int
