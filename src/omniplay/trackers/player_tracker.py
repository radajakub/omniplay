from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from omniplay.player.player import PlayerOutput


class PlayerTracker(ABC):
    @abstractmethod
    def record(self, player_output: PlayerOutput) -> dict[str, Any]:
        raise NotImplementedError


class NoOpTracker(PlayerTracker):
    def record(self, player_output: PlayerOutput) -> dict[str, Any]:
        return {}


class PlayerTrackerResolver(Protocol):
    def player_tracker(self, key: str) -> PlayerTracker:
        ...
