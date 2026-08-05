from __future__ import annotations

from dataclasses import dataclass

from plybench.analysis.recognition import recognizable, step_reasoning_trace, trace_mentions_original_game
from plybench.analysis.replay import build_replayer
from plybench.common.enums import StateClass
from plybench.registry import Registry
from plybench.trackers.result_tracker import ResultTracker


@dataclass(frozen=True)
class MoveRecord:
    """One judged move of the analysed player: its optimality/regret verdict, how forced the state was,
    its token cost, and whether the reasoning trace recognised the underlying game (None when the game
    is not recognisable or the move carried no trace). The unit both move-metrics and partitioners
    consume, so any move-level analysis works off one shared record."""

    state_class: StateClass
    is_optimal: bool
    regret: float
    input_tokens: int | None
    output_tokens: int | None
    recognized: bool | None
    n_legal: int = 0  # branching factor at this state
    n_optimal: int = 0  # size of the solver's optimal-action set at this state


def _recognized(trace: str | None, game_key: str) -> bool | None:
    if not recognizable(game_key) or trace is None:
        return None
    return trace_mentions_original_game(trace, game_key)


def collect_moves(tracker: ResultTracker, registry: Registry) -> list[MoveRecord]:
    """Replay every recorded game and build one MoveRecord per judged move of the analysed player. Only
    meaningful for solvable games (the replay judges against the solved minimax cache)."""
    replayer = build_replayer(registry, tracker.game)
    moves: list[MoveRecord] = []
    for game in tracker.games:
        if game is None:
            continue
        for judged in replayer.replay_judged(game, tracker.i):
            moves.append(
                MoveRecord(
                    state_class=judged.state_class,
                    is_optimal=judged.is_optimal,
                    regret=judged.regret,
                    input_tokens=judged.step.input_tokens,
                    output_tokens=judged.step.output_tokens,
                    recognized=_recognized(step_reasoning_trace(judged.step), tracker.game.key),
                    n_legal=judged.n_legal,
                    n_optimal=judged.n_optimal,
                )
            )
    return moves
