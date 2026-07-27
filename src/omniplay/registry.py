from __future__ import annotations

from omniplay.configs.game_config import GameConfig
from omniplay.configs.player_config import PlayerConfig
from omniplay.configs.player_params import PlayerParams
from omniplay.games.spec import GameSpec
from omniplay.trackers.player_tracker import NoOpTracker, PlayerTracker

from omniplay.core.engine import TurnBasedEngine


class Registry:
    """Instance-scoped plugin registry owned by an OmniPlay object (`op.registry`). Holds the games,
    player-params, and per-player trackers. External code extends it via register_game / register_player
    without touching the package, and there is no global mutable state."""

    def __init__(self) -> None:
        self._games: dict[str, GameSpec] = {}
        self._player_params: dict[str, type[PlayerParams]] = {}
        self._player_trackers: dict[str, PlayerTracker] = {}
        self._noop_tracker = NoOpTracker()

    # --- games ------------------------------------------------------------------------------
    def register_game(self, spec: GameSpec) -> None:
        self._games[spec.key] = spec

    def resolve_game(self, key: str) -> GameSpec:
        spec = self._games.get(key)
        if spec is None:
            raise ValueError(f'No game registered for key {key!r}; registered: {self.game_keys()}')
        return spec

    def game_keys(self) -> list[str]:
        return sorted(self._games)

    def game_config(self, config_string: str) -> GameConfig:
        key, _, params_string = config_string.partition(':')
        return GameConfig(key, self.resolve_game(key).params_cls.from_string(params_string))

    def build_engine(self, game_config: GameConfig) -> TurnBasedEngine:
        engine = self.resolve_game(game_config.key).engine_factory(game_config)
        engine.trackers = self
        return engine

    def solvable(self, key: str) -> bool:
        return self.resolve_game(key).solvable

    # --- player params ----------------------------------------------------------------------
    def register_player_params(self, key: str, params_cls: type[PlayerParams]) -> None:
        self._player_params[key] = params_cls

    def player_keys(self) -> list[str]:
        return sorted(self._player_params)

    def player_config(self, config_string: str) -> PlayerConfig:
        key, _, params_string = config_string.partition(':')
        params_cls = self._player_params.get(key)
        if params_cls is None:
            raise ValueError(f'No player registered for key {key!r}; registered: {self.player_keys()}')
        return PlayerConfig(key, params_cls.from_string(params_string))

    # --- per-player trackers ----------------------------------------------------------------
    def register_player_tracker(self, key: str, tracker: PlayerTracker) -> None:
        self._player_trackers[key] = tracker

    def player_tracker(self, key: str) -> PlayerTracker:
        return self._player_trackers.get(key, self._noop_tracker)
