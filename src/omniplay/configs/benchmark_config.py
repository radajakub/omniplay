from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from omniplay.common.serializable import Serializable
from omniplay.configs.toggle_item import ToggleItem

DEFAULT_OPPONENT = "optimal:stochastic=True"


@dataclass(frozen=True, eq=True)
class BenchmarkConfig(Serializable):
    game_configs: list[ToggleItem]
    player_configs: list[ToggleItem]
    opponent_configs: list[ToggleItem]
    num_games: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BenchmarkConfig:
        return cls(
            [ToggleItem.from_dict(game_config) for game_config in data["game_configs"]],
            [ToggleItem.from_dict(player_config) for player_config in data["player_configs"]],
            cls._parse_opponents(data),
            int(data["num_games"]),
        )

    @staticmethod
    def _parse_opponents(data: dict[str, Any]) -> list[ToggleItem]:
        if "opponents" in data:
            return [ToggleItem.from_dict(opponent) for opponent in data["opponents"]]

        # legacy single baseline -> one enabled opponent
        return [ToggleItem(data.get("baseline", DEFAULT_OPPONENT), True)]

    def get_game_configs(self) -> list[str]:
        return [item.value for item in self.game_configs if item.enabled]

    def get_player_configs(self) -> list[str]:
        return [item.value for item in self.player_configs if item.enabled]

    def get_opponent_configs(self) -> list[str]:
        return [item.value for item in self.opponent_configs if item.enabled]

    def to_dict(self) -> dict[str, Any]:
        return {
            "game_configs": [item.to_dict() for item in self.game_configs],
            "player_configs": [item.to_dict() for item in self.player_configs],
            "opponents": [item.to_dict() for item in self.opponent_configs],
            "num_games": self.num_games,
        }
