from __future__ import annotations

from plybench.analysis.extractors.base import Extractor
from plybench.analysis.extractors.suite import matchup_suite
from plybench.analysis.statistics.bundle import CIBundle, bundle_for_family
from plybench.analysis.stats.matchup_stats import MatchupMetrics, MatchupStats, Split
from plybench.configs.player_config import PlayerConfig
from plybench.registry import Registry
from plybench.trackers.game_tracker import GameTracker
from plybench.trackers.result_tracker import ResultTracker


def _bundle(extractor: Extractor, games: list[GameTracker], player: PlayerConfig, confidence: float) -> CIBundle:
    return bundle_for_family(extractor.family, extractor.extract(games, player), confidence)


def _metrics(extractors: list[Extractor], games: list[GameTracker], player: PlayerConfig, confidence: float) -> MatchupMetrics:
    return MatchupMetrics(len(games), {extractor.name: _bundle(extractor, games, player, confidence) for extractor in extractors})


def compute_matchup_metrics(tracker: ResultTracker, registry: Registry | None = None, confidence: float = 0.95, include_fails: bool = False) -> Split[MatchupMetrics]:
    extractors = matchup_suite(tracker, registry, include_fails)
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
