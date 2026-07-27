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
