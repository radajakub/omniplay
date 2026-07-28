from __future__ import annotations

from typing import Protocol

from omniplay.configs.game_config import GameConfig
from omniplay.configs.player_config import PlayerConfig


class ConfigParser(Protocol):
    def game_config(self, config_string: str) -> GameConfig:
        ...

    def player_config(self, config_string: str) -> PlayerConfig:
        ...
