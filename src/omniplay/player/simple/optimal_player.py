from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import cast

import numpy as np

from omniplay.common.paths import MinimaxPathBuilder
from omniplay.configs.player_config import PlayerConfig
from omniplay.configs.player_params import PlayerParams
from omniplay.core.game import TurnBasedGame
from omniplay.core.interface import InterfaceAction, InterfaceObservation
from omniplay.core.minimax import AVQ, AVQCache, solve_game
from omniplay.core.prompt_adapter import PromptAdapter
from omniplay.player.player import Player, PlayerIdentifier, PlayerOutput
from omniplay.utils.text import extract_params, to_bool


@dataclass(frozen=True, eq=True)
class OptimalParams(PlayerParams):
    stochastic: bool = False
    eps: float = 0.0

    @classmethod
    def from_string(cls, params_string: str) -> OptimalParams:
        params = extract_params(params_string)
        return cls(stochastic=to_bool(params.get('stochastic', False)), eps=float(params.get('eps', 0)))

    def to_string(self) -> str:
        return f'stochastic={self.stochastic}'

    @property
    def path_suffix(self) -> str:
        return 'stochastic' if self.stochastic else 'deterministic'


class Judgeable(ABC):
    @abstractmethod
    def optimal(self, player: int, observation: InterfaceObservation) -> AVQ | None:
        raise NotImplementedError


class OptimalPlayer(Player, Judgeable):
    def __init__(self, game: TurnBasedGame, player_config: PlayerConfig, identifier: PlayerIdentifier) -> None:
        super().__init__(player_config, identifier)

        self._params = cast(OptimalParams, player_config.params)

        self._cache: AVQCache | None = None

        self._path_builder = MinimaxPathBuilder()

    def initialize_policy(self, game: TurnBasedGame, prompt_adapter_template: PromptAdapter) -> None:
        # load the solved value cache from disk, or solve the game and persist it
        path = self._path_builder.cache(game.game_name, game.params)
        if path.exists():
            self._cache = AVQCache.load(str(path))
        else:
            self._cache = solve_game(game)
            self._cache.save(str(path))

    def _verdict(self, player: int, os_state: str) -> AVQ:
        assert self._cache is not None, 'Optimal policy not initialized'

        entry = self._cache[player, os_state]

        if entry is None:
            raise ValueError(f'Optimal action not found for state {os_state} and player {player}')

        return entry

    async def __call__(self, game: TurnBasedGame, observation: InterfaceObservation, legal_moves: list[InterfaceAction]) -> PlayerOutput:
        optimal_numbers = self._verdict(game.get_player(), observation.os_observation.state).A()

        if np.random.rand() < self._params.eps:
            return PlayerOutput(action=legal_moves[int(np.random.choice(len(legal_moves)))])

        number = int(np.random.choice(optimal_numbers)) if self._params.stochastic else optimal_numbers[0]

        action = next((move for move in legal_moves if move.number == number), None)

        return PlayerOutput(action=action)

    def optimal(self, player: int, observation: InterfaceObservation) -> AVQ | None:
        return self._verdict(player, observation.os_observation.state)

    def format_llm_output(self, player_output: PlayerOutput) -> str:
        return ''
