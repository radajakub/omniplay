from __future__ import annotations

from plybench.analysis.extractors.base import Extractor
from plybench.analysis.extractors.moves import MovesPerGameExtractor
from plybench.analysis.extractors.outcomes import OutcomeExtractor
from plybench.analysis.extractors.score import ScoreExtractor
from plybench.analysis.extractors.tokens import PerMoveTokensExtractor, TotalTokensExtractor
from plybench.common.enums import GameResults, MetricName


def default_suite(include_fails: bool = False) -> list[Extractor]:
    loss_targets = [GameResults.LOSS] + ([GameResults.MY_FAIL] if include_fails else [])
    return [
        OutcomeExtractor(MetricName.WIN_RATE, [GameResults.WIN]),
        OutcomeExtractor(MetricName.DRAW_RATE, [GameResults.DRAW]),
        OutcomeExtractor(MetricName.LOSS_RATE, loss_targets),
        OutcomeExtractor(MetricName.FAIL_RATE, [GameResults.MY_FAIL]),
        ScoreExtractor(),
        MovesPerGameExtractor(),
        TotalTokensExtractor(MetricName.INPUT_TOKENS_PER_GAME, 'input_tokens'),
        TotalTokensExtractor(MetricName.OUTPUT_TOKENS_PER_GAME, 'output_tokens'),
        PerMoveTokensExtractor(MetricName.INPUT_TOKENS_PER_MOVE, 'input_tokens'),
        PerMoveTokensExtractor(MetricName.OUTPUT_TOKENS_PER_MOVE, 'output_tokens'),
    ]
