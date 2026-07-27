from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from omniplay.common.enums import Games
from omniplay.utils.text import extract_params, to_bool


@dataclass(frozen=True, eq=True)
class GameConfig:
    game_type: Games
    sample: bool = False

    # tic tac toe / magic square configuration
    magic_constant_add: int = 0
    # nim configuration
    num_piles: int = 4
    max_pile_size: int = 8
    pile_sum: int = 16
    nim_start: Literal['winning', 'losing'] = 'winning'

    @classmethod
    def from_string(cls, config_string: str) -> GameConfig:
        parts = config_string.split(':')
        if len(parts) != 2:
            raise ValueError('Invalid game config, must be in format <game>:<params>')

        game_string, params_string = parts
        game_type = Games.from_value(game_string)
        if game_type is None:
            raise ValueError(f'Invalid game type: {game_string}')

        params = extract_params(params_string)
        return cls(
            game_type,
            sample=to_bool(params.get('sample', False)),
            magic_constant_add=int(params.get('magic_constant_add', 0)),
            num_piles=int(params.get('num_piles', 4)),
            max_pile_size=int(params.get('max_pile_size', 8)),
            pile_sum=int(params.get('pile_sum', 16)),
            nim_start=params.get('nim_start', 'winning'),
        )

    def to_string(self) -> str:
        match self.game_type:
            case Games.MAGIC_SQUARE | Games.STORY_MAGIC_SQUARE:
                return f'{self.game_type.value}:sample={self.sample},magic_constant_add={self.magic_constant_add}'
            case Games.NIM | Games.INVERSE_NIM | Games.STORY_NIM:
                if self.sample:
                    return (f'{self.game_type.value}:sample=True,num_piles={self.num_piles},'
                            f'max_pile_size={self.max_pile_size},pile_sum={self.pile_sum},nim_start={self.nim_start}')
                return f'{self.game_type.value}:'
            case _:
                return f'{self.game_type.value}:'

    @property
    def path(self) -> str:
        match self.game_type:
            case Games.MAGIC_SQUARE | Games.STORY_MAGIC_SQUARE:
                return f'{self.game_type.value}_{"sample" if self.sample else "normal"}_add_{self.magic_constant_add}'
            case Games.NIM | Games.INVERSE_NIM | Games.STORY_NIM:
                if self.sample:
                    return (f'{self.game_type.value}_sample_{self.num_piles}_piles_'
                            f'{self.max_pile_size}_max_size_{self.pile_sum}_sum_{self.nim_start}')
                return self.game_type.value
            case _:
                return self.game_type.value

    @property
    def sort_key(self) -> tuple[int, int, bool]:
        return (list(Games).index(self.game_type), self.magic_constant_add, self.sample)
