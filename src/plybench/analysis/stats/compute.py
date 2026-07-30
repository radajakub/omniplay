from __future__ import annotations

from plybench.analysis.extractors.base import Extractor
from plybench.analysis.extractors.quality import quality_extractors
from plybench.analysis.extractors.suite import default_suite
from plybench.analysis.statistics.bundle import CIBundle, mean_bundle, ratio_bundle
from plybench.analysis.stats.matchup_stats import MatchupMetrics, MatchupStats, Split
from plybench.common.enums import CIFamily
from plybench.configs.player_config import PlayerConfig
from plybench.registry import Registry
from plybench.trackers.game_tracker import GameTracker
from plybench.trackers.result_tracker import ResultTracker


def _bundle(extractor: Extractor, games: list[GameTracker], player: PlayerConfig, confidence: float) -> CIBundle:
    distribution = extractor.extract(games, player)
    if extractor.family == CIFamily.RATIO:
        return ratio_bundle(distribution, confidence)
    return mean_bundle(distribution, confidence)


def _metrics(extractors: list[Extractor], games: list[GameTracker], player: PlayerConfig, confidence: float) -> MatchupMetrics:
    return MatchupMetrics(len(games), {extractor.name: _bundle(extractor, games, player, confidence) for extractor in extractors})


def _extractors(tracker: ResultTracker, registry: Registry | None, include_fails: bool) -> list[Extractor]:
    extractors = default_suite(include_fails)
    # optimality/regret need a solved minimax cache, so only for solvable games and when a registry
    # (to build the engine + optimal judge) is supplied
    if registry is not None and registry.solvable(tracker.game.key):
        extractors += quality_extractors(registry, tracker.game, tracker.i)
    return extractors


def compute_matchup_metrics(tracker: ResultTracker, registry: Registry | None = None, confidence: float = 0.95, include_fails: bool = False) -> Split[MatchupMetrics]:
    extractors = _extractors(tracker, registry, include_fails)
    games = [game for game in tracker.games if game is not None]
    player = tracker.i  # metrics are always from the analysed player's (i) POV, vs the opponent (o)

    i_first, i_second = ResultTracker.split_games_by_starting_player(games, player)
    return Split(
        combined=_metrics(extractors, games, player, confidence),
        i_first=_metrics(extractors, i_first, player, confidence),
        i_second=_metrics(extractors, i_second, player, confidence),
    )


def compute_matchup_stats(tracker: ResultTracker, registry: Registry | None = None, confidence: float = 0.95, include_fails: bool = False) -> MatchupStats:
    metrics = compute_matchup_metrics(tracker, registry, confidence, include_fails)
    return MatchupStats(tracker.experiment, tracker.i, tracker.o, tracker.game, tracker.n, sorted(tracker.completed), metrics)
