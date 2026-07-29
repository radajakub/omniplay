from __future__ import annotations

from dataclasses import dataclass

from omniplay.configs.player_params import PlayerParams
from omniplay.core.game import TurnBasedGame
from omniplay.core.interface import InterfaceAction, InterfaceObservation
from omniplay.core.prompt_adapter import PromptAdapter
from omniplay.player.player import Player, PlayerOutput


@dataclass(frozen=True, eq=True)
class HumanParams(PlayerParams):
    @classmethod
    def from_string(cls, params_string: str) -> HumanParams:
        return cls()

    def to_string(self) -> str:
        return ""

    @property
    def path_suffix(self) -> str:
        return ""


class HumanPlayer(Player):
    def initialize_policy(self, game: TurnBasedGame, prompt_adapter_template: PromptAdapter) -> None:
        pass

    @staticmethod
    def _lookup_move(legal_moves: list[InterfaceAction], move_string: str) -> InterfaceAction | None:
        for move in legal_moves:
            if str(move) == move_string or str(move) == f"{move_string}*":
                return move
        return None

    async def __call__(self, game: TurnBasedGame, observation: InterfaceObservation, legal_moves: list[InterfaceAction]) -> PlayerOutput:
        print("Current observation:")
        print(observation)
        print("Legal moves:")

        for i, move in enumerate(legal_moves):
            print(f"{i + 1:>2}. {move}")

        chosen = input("Enter the move string to play: ").strip()

        return PlayerOutput(action=self._lookup_move(legal_moves, chosen))

    def format_llm_output(self, player_output: PlayerOutput) -> str:
        return ""
