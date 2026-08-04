from __future__ import annotations

from plybench.analysis.extractors.base import Extractor
from plybench.analysis.extractors.moves import MovesPerGameExtractor
from plybench.analysis.extractors.outcomes import OutcomeExtractor
from plybench.analysis.extractors.quality import quality_extractors
from plybench.analysis.extractors.recognition import recognition_extractors
from plybench.analysis.extractors.score import ScoreExtractor
from plybench.analysis.extractors.tokens import PerMoveTokensExtractor, TotalTokensExtractor
from plybench.common.enums import GameResults, MetricName
from plybench.registry import Registry
from plybench.trackers.result_tracker import ResultTracker


def default_suite(include_fails: bool = False) -> list[Extractor]:
    """The game-agnostic extractors: outcomes, score, moves and tokens, all read straight off the
    recorded games. Every matchup gets these."""
    loss_targets = [GameResults.LOSS] + ([GameResults.MY_FAIL] if include_fails else [])
    return [
        OutcomeExtractor(MetricName.WIN_RATE, [GameResults.WIN]),
        OutcomeExtractor(MetricName.DRAW_RATE, [GameResults.DRAW]),
        OutcomeExtractor(MetricName.LOSS_RATE, loss_targets),
        OutcomeExtractor(MetricName.FAIL_RATE, [GameResults.MY_FAIL]),
        ScoreExtractor(),
        MovesPerGameExtractor(),
        TotalTokensExtractor(MetricName.INPUT_TOKENS_PER_GAME, "input_tokens"),
        TotalTokensExtractor(MetricName.OUTPUT_TOKENS_PER_GAME, "output_tokens"),
        PerMoveTokensExtractor(MetricName.INPUT_TOKENS_PER_MOVE, "input_tokens"),
        PerMoveTokensExtractor(MetricName.OUTPUT_TOKENS_PER_MOVE, "output_tokens"),
    ]


def matchup_suite(tracker: ResultTracker, registry: Registry | None = None, include_fails: bool = False) -> list[Extractor]:
    """Everything computable for one matchup: the default suite plus the groups whose preconditions the
    matchup happens to meet. Recognition needs only a recognisable original game; optimality/regret need
    a solved minimax cache, so a solvable game and a registry to build the engine and the optimal judge."""
    extractors = default_suite(include_fails)
    extractors += recognition_extractors(tracker.game.key)
    if registry is not None and registry.solvable(tracker.game.key):
        extractors += quality_extractors(registry, tracker.game, tracker.i)
    return extractors
