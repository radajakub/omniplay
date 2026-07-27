from __future__ import annotations

from omniplay.utils.enums import ExtendedEnum


class PlayerOrder(ExtendedEnum):
    FIRST = 'first'
    SECOND = 'second'

    @staticmethod
    def from_int(player: int) -> PlayerOrder:
        if player == 0:
            return PlayerOrder.FIRST
        elif player == 1:
            return PlayerOrder.SECOND
        raise ValueError('Player has to be either 0 or 1')

    def is_first(self) -> bool:
        return self == PlayerOrder.FIRST


class Games(ExtendedEnum):
    # classic tic tac toe game on a 3x3 grid
    TIC_TAC_TOE = 'tic_tac_toe'
    # tic tac toe with a modified prompt (game name hidden, 'X'/'O' shown as 'B'/'W')
    MODIFIED_TIC_TAC_TOE = 'modified_tic_tac_toe'
    # magic square modification of tic tac toe: 3x3 numbers, get three summing to a constant
    MAGIC_SQUARE = 'magic_square'
    # magic square framed as a story
    STORY_MAGIC_SQUARE = 'story_magic_square'
    # classic misere nim with 1,3,5,7 piles (or sampled per round)
    NIM = 'nim'
    # nim with a modified prompt (game name hidden, actions slightly changed)
    MODIFIED_NIM = 'modified_nim'
    # inverse nim: add to piles instead of removing
    INVERSE_NIM = 'inverse_nim'
    # nim framed as a story
    STORY_NIM = 'story_nim'
    # connect four on a standard grid
    CONNECT_FOUR = 'connect_four'
    # breakthrough on an 8x3 grid, reach the opponent's home row first
    BREAKTHROUGH = 'breakthrough'

    @property
    def solvable(self) -> bool:
        """Whether the game tree is small enough to solve with minimax."""
        return self in _SOLVABLE_GAMES


_SOLVABLE_GAMES = {
    Games.TIC_TAC_TOE,
    Games.MODIFIED_TIC_TAC_TOE,
    Games.MAGIC_SQUARE,
    Games.STORY_MAGIC_SQUARE,
    Games.NIM,
    Games.MODIFIED_NIM,
    Games.INVERSE_NIM,
    Games.STORY_NIM,
}


class ObservationType(ExtendedEnum):
    ACTIONS = 'actions'
    STATE = 'state'


class OutputStrategies(ExtendedEnum):
    TEXT = 'text'
    STRUCTURED = 'structured'


class GameResults(ExtendedEnum):
    WIN = 0
    LOSS = 1
    DRAW = 2
    MY_FAIL = 3
    OPPONENT_FAIL = 4

    def invert(self) -> GameResults:
        return {
            GameResults.WIN: GameResults.LOSS,
            GameResults.LOSS: GameResults.WIN,
            GameResults.DRAW: GameResults.DRAW,
            GameResults.MY_FAIL: GameResults.OPPONENT_FAIL,
            GameResults.OPPONENT_FAIL: GameResults.MY_FAIL,
        }[self]

    def to_reward(self) -> float:
        return {
            GameResults.WIN: 1.0,
            GameResults.DRAW: 0.5,
            GameResults.LOSS: 0.0,
            GameResults.MY_FAIL: -1.0,
            GameResults.OPPONENT_FAIL: 0.0,
        }[self]

    def to_prompt(self) -> str:
        return {
            GameResults.WIN: 'WON',
            GameResults.LOSS: 'LOST',
            GameResults.DRAW: 'DRAW',
            GameResults.MY_FAIL: 'LOST (failed to produce a valid move)',
            GameResults.OPPONENT_FAIL: 'WON (opponent failed to produce a valid move)',
        }[self]


class StateClass(ExtendedEnum):
    DONT_CARE = 'dont_care'  # all legal moves optimal AND state value > LOSS — forced non-losing
    LOST = 'lost'            # all legal moves optimal AND state value == LOSS — already lost
    DECISION = 'decision'    # optimal set is a strict subset of legal moves — a real choice exists

    @property
    def is_forced(self) -> bool:
        return self in (StateClass.DONT_CARE, StateClass.LOST)
