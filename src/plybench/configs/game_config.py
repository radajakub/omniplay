from __future__ import annotations

from dataclasses import dataclass

from plybench.configs.game_params import GameParams


@dataclass(frozen=True, eq=True)
class GameConfig:
    key: str
    params: GameParams

    def to_string(self) -> str:
        return f"{self.key}:{self.params.to_string()}"

    @property
    def path(self) -> str:
        suffix = self.params.path_suffix
        return f"{self.key}_{suffix}" if suffix else self.key

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return self.__str__()
