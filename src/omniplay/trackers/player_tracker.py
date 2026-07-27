from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

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


# plugin registry: player key -> the tracker that decides what extras to persist for that player type.
# Unregistered keys (e.g. simple bots) fall back to the no-op tracker.
_TRACKER_REGISTRY: dict[str, PlayerTracker] = {}
_NOOP = NoOpTracker()


def register_player_tracker(key: str, tracker: PlayerTracker) -> None:
    _TRACKER_REGISTRY[key] = tracker


def resolve_player_tracker(key: str) -> PlayerTracker:
    return _TRACKER_REGISTRY.get(key, _NOOP)
