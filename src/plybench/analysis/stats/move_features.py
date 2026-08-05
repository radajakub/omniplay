from __future__ import annotations

from collections.abc import Callable, Sequence

from plybench.analysis.stats.moves import MoveRecord
from plybench.common.enums import StateClass

MoveFeature = Callable[[MoveRecord], float]


def branching(move: MoveRecord) -> float:
    """Number of legal actions at the state. The phase-confounded axis: in games like tic-tac-toe the
    action count is pinned to the ply, so a token<-branching slope is partly a token<-game-phase slope,
    not pure search cost."""
    return float(move.n_legal)


def sharpness(move: MoveRecord) -> float:
    """Solver-derived tactical difficulty: the fraction of legal moves that are NOT optimal. 0 means
    every legal move is optimal (trivial); values near 1 mean a single move is optimal among many (very
    sharp). The graded form of the non-trivial decision filter, and it varies within a fixed branching
    bin, so it disentangles difficulty from game phase."""
    if move.n_legal <= 0:
        return 0.0
    return 1.0 - move.n_optimal / move.n_legal


# Named features that are defined for every judged move, so they can bin any move list without an
# applicability guard -- unlike recognition, which needs a recognisable game and a reasoning trace.
UNGUARDED_FEATURES: tuple[tuple[str, MoveFeature], ...] = (("sharpness", sharpness), ("branching", branching))


def decision_moves(moves: Sequence[MoveRecord]) -> list[MoveRecord]:
    """Restrict to genuine decision points that carry a token count: the only moves where difficulty is
    defined (optimal set a strict subset of legal) and where token spend is observed."""
    return [m for m in moves if m.state_class == StateClass.DECISION and m.output_tokens is not None]
