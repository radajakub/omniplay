from __future__ import annotations

import hashlib
from dataclasses import dataclass

from omniplay.configs.player_params import PlayerParams, resolve_player_params


@dataclass(frozen=True, eq=True)
class PlayerConfig:
    key: str
    params: PlayerParams

    @classmethod
    def from_string(cls, config_string: str) -> PlayerConfig:
        key, _, params_string = config_string.partition(':')
        params_cls = resolve_player_params(key)
        return cls(key, params_cls.from_string(params_string))

    def to_string(self) -> str:
        return f'{self.key}:{self.params.to_string()}'

    @property
    def path(self) -> str:
        return self.params.path

    @property
    def hash(self) -> str:
        # short, deterministic id derived from the canonical serialization; used only to match a
        # player to its recorded steps (stable across processes, unlike builtin hash()).
        return hashlib.sha256(self.to_string().encode()).hexdigest()[:12]

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return self.__str__()
