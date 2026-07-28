from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from omniplay.common.enums import GameResults
from omniplay.configs.player_config import PlayerConfig
from omniplay.core.interface import InterfaceAction, InterfaceObservation

from omniplay.player.player import Player, PlayerOutput
from omniplay.trackers.game_tracker import GameStep, GameTracker

# Game-loop phase hooks. An agent (or any caller) supplies these to observe the game as it plays;
# they never mutate game state. All slots are optional and null-guarded (default GameCallbacks() = no-op).
GameStartCallback = Callable[['GameTracker'], None]
BeforeMoveCallback = Callable[['Player', InterfaceObservation, list[InterfaceAction]], None]
AfterMoveCallback = Callable[['Player', 'PlayerOutput', 'GameStep'], None]
GameEndCallback = Callable[['GameTracker', tuple[GameResults, GameResults]], None]


@dataclass
class GameCallbacks:
    game_start_callback: GameStartCallback | None = None
    before_move_callback: BeforeMoveCallback | None = None
    after_move_callback: AfterMoveCallback | None = None
    game_end_callback: GameEndCallback | None = None

    def on_game_start(self, tracker: GameTracker) -> None:
        if self.game_start_callback is not None:
            self.game_start_callback(tracker)

    def on_before_move(self, player: Player, observation: InterfaceObservation, legal_moves: list[InterfaceAction]) -> None:
        if self.before_move_callback is not None:
            self.before_move_callback(player, observation, legal_moves)

    def on_after_move(self, player: Player, player_output: PlayerOutput, step: GameStep) -> None:
        if self.after_move_callback is not None:
            self.after_move_callback(player, player_output, step)

    def on_game_end(self, tracker: GameTracker, results: tuple[GameResults, GameResults]) -> None:
        if self.game_end_callback is not None:
            self.game_end_callback(tracker, results)

    @classmethod
    def combine(cls, *bundles: GameCallbacks | None) -> GameCallbacks:
        children = tuple(bundle for bundle in bundles if bundle is not None)

        def fan(method_name: str) -> Callable[..., None]:
            def call(*args: object) -> None:
                for child in children:
                    getattr(child, method_name)(*args)
            return call

        return cls(
            game_start_callback=fan('on_game_start'),
            before_move_callback=fan('on_before_move'),
            after_move_callback=fan('on_after_move'),
            game_end_callback=fan('on_game_end'),
        )

    @staticmethod
    def for_player(player_config: PlayerConfig, bundle: GameCallbacks) -> GameCallbacks:
        def scoped_before(player: Player, observation: InterfaceObservation, legal_moves: list[InterfaceAction]) -> None:
            if player.player_config.hash == player_config.hash:
                bundle.on_before_move(player, observation, legal_moves)

        def scoped_after(player: Player, player_output: PlayerOutput, step: GameStep) -> None:
            if player.player_config.hash == player_config.hash:
                bundle.on_after_move(player, player_output, step)

        return GameCallbacks(
            game_start_callback=lambda tracker: bundle.on_game_start(tracker),
            before_move_callback=scoped_before,
            after_move_callback=scoped_after,
            game_end_callback=lambda tracker, results: bundle.on_game_end(tracker, results),
        )
