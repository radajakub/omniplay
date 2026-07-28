from __future__ import annotations

from typing import Protocol

from omniplay.configs.game_config import GameConfig
from omniplay.configs.player_config import PlayerConfig


class ConfigParser(Protocol):
    """What deserialization needs to turn config strings into typed configs. The Registry satisfies
    this structurally, so trackers depend on this narrow interface rather than on the Registry."""

    def game_config(self, config_string: str) -> GameConfig:
        ...

    def player_config(self, config_string: str) -> PlayerConfig:
        ...
