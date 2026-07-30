from __future__ import annotations

from typing import Protocol

from plybench.configs.game_config import GameConfig
from plybench.configs.player_config import PlayerConfig


class ConfigParser(Protocol):
    def game_config(self, config_string: str) -> GameConfig: ...

    def player_config(self, config_string: str) -> PlayerConfig: ...
