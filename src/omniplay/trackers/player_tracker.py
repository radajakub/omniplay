from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from omniplay.player.player import PlayerOutput


class PlayerTracker(ABC):
    """Produces the player-specific extras persisted on a GameStep's `data` field for a given player
    type. Tokens are recorded generically by the tracker framework and are NOT this class's concern;
    concrete trackers (e.g. an LLM/agent tracker recording the reasoning trace) live with their
    players and register themselves by key."""

    @abstractmethod
    def record(self, player_output: PlayerOutput) -> dict[str, Any]:
        raise NotImplementedError


class NoOpTracker(PlayerTracker):
    def record(self, player_output: PlayerOutput) -> dict[str, Any]:
        return {}


class PlayerTrackerResolver(Protocol):
    """What the engine/tracker needs to look up a player's tracker by key. The Registry satisfies
    this structurally, so the engine/game-tracker depend on this narrow interface, not on Registry."""

    def player_tracker(self, key: str) -> PlayerTracker: ...
