from __future__ import annotations

from omniplay.analysis.extractors.base import Extractor
from omniplay.analysis.extractors.moves import MovesPerGameExtractor
from omniplay.analysis.extractors.outcomes import OutcomeExtractor
from omniplay.analysis.extractors.score import ScoreExtractor
from omniplay.analysis.extractors.tokens import PerMoveTokensExtractor, TotalTokensExtractor
from omniplay.common.enums import GameResults, MetricName


def default_suite(include_fails: bool = False) -> list[Extractor]:
    """The benchmark metric suite computed purely from recorded fields (no replay). `include_fails`
    folds the analysed player's own failed games into the loss rate."""
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
