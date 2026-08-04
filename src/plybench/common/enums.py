from __future__ import annotations

from plybench.utils.enums import ExtendedEnum


class PlayerOrder(ExtendedEnum):
    FIRST = "first"
    SECOND = "second"

    @staticmethod
    def from_int(player: int) -> PlayerOrder:
        if player == 0:
            return PlayerOrder.FIRST
        elif player == 1:
            return PlayerOrder.SECOND
        raise ValueError("Player has to be either 0 or 1")

    def is_first(self) -> bool:
        return self == PlayerOrder.FIRST


class ObservationType(ExtendedEnum):
    ACTIONS = "actions"
    STATE = "state"


class OutputStrategies(ExtendedEnum):
    TEXT = "text"
    STRUCTURED = "structured"


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
            GameResults.WIN: "WON",
            GameResults.LOSS: "LOST",
            GameResults.DRAW: "DRAW",
            GameResults.MY_FAIL: "LOST (failed to produce a valid move)",
            GameResults.OPPONENT_FAIL: "WON (opponent failed to produce a valid move)",
        }[self]


class StateClass(ExtendedEnum):
    DONT_CARE = "dont_care"  # all legal moves optimal AND state value > LOSS — forced non-losing
    LOST = "lost"  # all legal moves optimal AND state value == LOSS — already lost
    DECISION = "decision"  # optimal set is a strict subset of legal moves — a real choice exists

    @property
    def is_forced(self) -> bool:
        return self in (StateClass.DONT_CARE, StateClass.LOST)


class CIFamily(ExtendedEnum):
    RATIO = "ratio"  # a proportion in [0, 1] -> Wilson interval
    MEAN = "mean"  # a real-valued mean -> SEM / t / bootstrap intervals


class MetricName(ExtendedEnum):
    WIN_RATE = "win_rate"
    DRAW_RATE = "draw_rate"
    LOSS_RATE = "loss_rate"
    FAIL_RATE = "fail_rate"
    SCORE = "score"
    MOVES_PER_GAME = "moves_per_game"
    INPUT_TOKENS_PER_GAME = "input_tokens_per_game"
    OUTPUT_TOKENS_PER_GAME = "output_tokens_per_game"
    INPUT_TOKENS_PER_MOVE = "input_tokens_per_move"
    OUTPUT_TOKENS_PER_MOVE = "output_tokens_per_move"
    # produced only for solvable games via replay (Phase 6b)
    OPTIMALITY_RATE = "optimality_rate"
    OPTIMALITY_RATE_NON_TRIVIAL = "optimality_rate_non_trivial"
    REGRET = "regret"
    # produced only for recognisable games from reasoning traces (Phase 6c)
    RECOGNITION_RATE = "recognition_rate"
