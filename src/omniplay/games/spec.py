from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from omniplay.configs.game_config import GameConfig
from omniplay.configs.game_params import GameParams
from omniplay.core.engine import TurnBasedEngine


@dataclass(frozen=True)
class GameSpec:
    key: str
    params_cls: type[GameParams]
    engine_factory: Callable[[GameConfig], TurnBasedEngine]
    # whether the game tree is small enough to solve with minimax (enables optimality/regret analysis)
    solvable: bool
