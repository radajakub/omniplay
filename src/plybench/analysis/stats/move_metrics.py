from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from plybench.analysis.statistics.bundle import CIBundle, bundle_for_family
from plybench.analysis.statistics.comparison import GroupComparison, compare_for_family
from plybench.analysis.statistics.distribution import Distribution
from plybench.analysis.stats.moves import MoveRecord
from plybench.common.enums import CIFamily, MetricName, StateClass


@dataclass(frozen=True)
class MoveMetric:
    """A move-level statistic: how to read one number off a MoveRecord (None = not applicable for this
    move, so it drops out of the sample) and which family it belongs to. Ratio metrics return 0.0/1.0
    indicators, mean metrics return real values. The family alone decides both the intervals and the
    between-group test, so callers never pick a test themselves."""

    name: MetricName
    family: CIFamily
    value: Callable[[MoveRecord], float | None]

    def distribution(self, moves: Sequence[MoveRecord]) -> Distribution:
        return Distribution([v for v in (self.value(move) for move in moves) if v is not None])

    def bundle(self, moves: Sequence[MoveRecord], confidence: float = 0.95) -> CIBundle:
        return bundle_for_family(self.family, self.distribution(moves), confidence)

    def compare(self, moves_a: Sequence[MoveRecord], moves_b: Sequence[MoveRecord], confidence: float = 0.95) -> GroupComparison:
        return compare_for_family(self.family, self.distribution(moves_a), self.distribution(moves_b), confidence)


def _optimality(move: MoveRecord) -> float:
    return 1.0 if move.is_optimal else 0.0


def _optimality_non_trivial(move: MoveRecord) -> float | None:
    return _optimality(move) if move.state_class == StateClass.DECISION else None


def _output_tokens(move: MoveRecord) -> float | None:
    return None if move.output_tokens is None else float(move.output_tokens)


DEFAULT_MOVE_METRICS: tuple[MoveMetric, ...] = (
    MoveMetric(MetricName.OPTIMALITY_RATE, CIFamily.RATIO, _optimality),
    MoveMetric(MetricName.OPTIMALITY_RATE_NON_TRIVIAL, CIFamily.RATIO, _optimality_non_trivial),
    MoveMetric(MetricName.REGRET, CIFamily.MEAN, lambda move: move.regret),
    MoveMetric(MetricName.OUTPUT_TOKENS_PER_MOVE, CIFamily.MEAN, _output_tokens),
)
