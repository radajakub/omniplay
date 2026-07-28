from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from omniplay.configs.player_config import PlayerConfig
from omniplay.configs.player_params import PlayerParams
from omniplay.core.game import TurnBasedGame
from omniplay.player.player import Player, PlayerIdentifier
from omniplay.trackers.player_tracker import PlayerTracker


@dataclass(frozen=True)
class PlayerSpec:
    key: str
    params_cls: type[PlayerParams]
    # builds the player for a game; the LLM (for AI/agents) is captured in this closure at registration
    build: Callable[[TurnBasedGame, PlayerConfig, PlayerIdentifier], Player]
    # optional per-player tracker deciding what extras to persist on each GameStep
    tracker: PlayerTracker | None = None
