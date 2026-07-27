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
