from __future__ import annotations

from abc import ABC, abstractmethod


class PlayerParams(ABC):
    @classmethod
    @abstractmethod
    def from_string(cls, params_string: str) -> PlayerParams:
        raise NotImplementedError

    @abstractmethod
    def to_string(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def path(self) -> str:
        raise NotImplementedError


# plugin registry mapping a player key -> its params class. Built-in and external players register
# their params class here (done by OmniPlay bootstrap in a later phase); deserialization looks it up.
_PARAMS_REGISTRY: dict[str, type[PlayerParams]] = {}


def register_player_params(key: str, params_cls: type[PlayerParams]) -> None:
    _PARAMS_REGISTRY[key] = params_cls


def resolve_player_params(key: str) -> type[PlayerParams]:
    params_cls = _PARAMS_REGISTRY.get(key)
    if params_cls is None:
        raise ValueError(
            f'No player params registered for key {key!r}; registered keys: {sorted(_PARAMS_REGISTRY)}'
        )
    return params_cls


def registered_player_keys() -> list[str]:
    return sorted(_PARAMS_REGISTRY)
