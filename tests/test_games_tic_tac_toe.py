"""Phase 3 end-to-end check: drive tic-tac-toe through engine.play with random players,
verify legal-move round-tripping and terminal detection."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass

from plybench.common.enums import GameResults
from plybench.configs.player_config import PlayerConfig
from plybench.configs.player_params import PlayerParams
from plybench.core.game import TurnBasedGame
from plybench.core.interface import InterfaceAction, InterfaceObservation
from plybench.core.prompt_adapter import PromptAdapter
from plybench.games.builtins import register_builtin_games
from plybench.games.tic_tac_toe.tic_tac_toe import TicTacToeAction, TicTacToeEngine
from plybench.player.player import Player, PlayerOutput
from plybench.registry import Registry

registry = Registry()
register_builtin_games(registry)


@dataclass(frozen=True)
class _RandParams(PlayerParams):
    seed: str

    @classmethod
    def from_string(cls, params_string: str) -> "_RandParams":
        return cls(params_string)

    def to_string(self) -> str:
        return self.seed

    @property
    def path_suffix(self) -> str:
        return self.seed


class _RandomPlayer(Player):
    def __init__(self, player_config: PlayerConfig, identifier, seed: int) -> None:
        super().__init__(player_config, identifier)
        self._rng = random.Random(seed)

    def initialize_policy(self, game: TurnBasedGame, prompt_adapter_template: PromptAdapter) -> None:
        pass

    async def __call__(self, game, observation: InterfaceObservation, legal_moves: list[InterfaceAction]) -> PlayerOutput:
        return PlayerOutput(action=self._rng.choice(legal_moves))

    def format_llm_output(self, player_output: PlayerOutput) -> str:
        return ""


def _players() -> tuple[_RandomPlayer, _RandomPlayer]:
    i = PlayerConfig("rand", _RandParams("1"))
    o = PlayerConfig("rand", _RandParams("2"))
    return _RandomPlayer(i, "i", seed=1), _RandomPlayer(o, "o", seed=2)


def test_tic_tac_toe_action_round_trips():
    engine = TicTacToeEngine(registry.game_config("tic_tac_toe:"))
    engine.reset()
    pid = engine.game.get_player()
    os_moves = engine.game.get_legal_moves(pid)
    assert len(os_moves) == 9  # empty board

    for move in os_moves:
        action = TicTacToeAction.from_openspiel(move, engine.interface_transformer)
        # to_openspiel preserves the action number and re-parses identically
        assert action.to_openspiel().number == move.number
        reparsed = TicTacToeAction.from_openspiel(action.to_openspiel(), engine.interface_transformer)
        assert (reparsed.row, reparsed.col, reparsed.number) == (action.row, action.col, action.number)


def test_tic_tac_toe_plays_to_terminal():
    engine = registry.build_engine(registry.game_config("tic_tac_toe:"))
    tracker = asyncio.run(engine.play(_players()))

    assert tracker.ending is not None
    assert tracker.ending.result in {GameResults.WIN, GameResults.LOSS, GameResults.DRAW}
    # tic-tac-toe lasts between 5 and 9 plies; no failed (illegal) moves from a random legal picker
    assert 5 <= len(tracker.steps) <= 9
    assert all(not step.move.startswith("FAIL") for step in tracker.steps)
    # a bot records no tokens
    assert all(step.input_tokens is None and step.output_tokens is None for step in tracker.steps)
