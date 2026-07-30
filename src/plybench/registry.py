from __future__ import annotations

from plybench.configs.game_config import GameConfig
from plybench.configs.player_config import PlayerConfig
from plybench.core.engine import TurnBasedEngine
from plybench.core.game import TurnBasedGame
from plybench.games.spec import GameSpec
from plybench.player.player import Player, PlayerIdentifier
from plybench.player.spec import PlayerSpec
from plybench.trackers.player_tracker import NoOpTracker, PlayerTracker


class Registry:
    def __init__(self) -> None:
        self._games: dict[str, GameSpec] = {}
        self._players: dict[str, PlayerSpec] = {}
        self._noop_tracker = NoOpTracker()

    # --- games ------------------------------------------------------------------------------
    def register_game(self, spec: GameSpec) -> None:
        self._games[spec.key] = spec

    def resolve_game(self, key: str) -> GameSpec:
        spec = self._games.get(key)
        if spec is None:
            raise ValueError(f"No game registered for key {key!r}; registered: {self.game_keys()}")
        return spec

    def game_keys(self) -> list[str]:
        return sorted(self._games)

    def game_config(self, config_string: str) -> GameConfig:
        key, _, params_string = config_string.partition(":")
        return GameConfig(key, self.resolve_game(key).params_cls.from_string(params_string))

    def build_engine(self, game_config: GameConfig) -> TurnBasedEngine:
        engine = self.resolve_game(game_config.key).engine_factory(game_config)
        engine.trackers = self
        return engine

    def solvable(self, key: str) -> bool:
        return self.resolve_game(key).solvable

    # --- players ----------------------------------------------------------------------------
    def register_player(self, spec: PlayerSpec) -> None:
        self._players[spec.key] = spec

    def resolve_player(self, key: str) -> PlayerSpec:
        spec = self._players.get(key)
        if spec is None:
            raise ValueError(f"No player registered for key {key!r}; registered: {self.player_keys()}")
        return spec

    def player_keys(self) -> list[str]:
        return sorted(self._players)

    def player_config(self, config_string: str) -> PlayerConfig:
        key, _, params_string = config_string.partition(":")
        return PlayerConfig(key, self.resolve_player(key).params_cls.from_string(params_string))

    def build_player(self, game: TurnBasedGame, player_config: PlayerConfig, identifier: PlayerIdentifier) -> Player:
        return self.resolve_player(player_config.key).build(game, player_config, identifier)

    def player_tracker(self, key: str) -> PlayerTracker:
        spec = self._players.get(key)
        return spec.tracker if spec is not None and spec.tracker is not None else self._noop_tracker
