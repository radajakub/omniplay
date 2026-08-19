"""Pooling a metric over a group of matchups into one value with a confidence interval.

Sits above the extractors and the interval estimators and below anything that presents a number:
a plot, a table and a report all want the same pooled value, so it lives outside all three."""

from __future__ import annotations

from dataclasses import dataclass

from plybench.analysis.extractors.base import Extractor
from plybench.analysis.extractors.suite import matchup_suite
from plybench.analysis.statistics.bundle import CIBundle, bundle_for_family
from plybench.common.enums import MetricName
from plybench.registry import Registry
from plybench.trackers.game_tracker import GameTracker
from plybench.trackers.result_tracker import ResultTracker
from plybench.utils.enums import ExtendedEnum


class GameSplit(ExtendedEnum):
    COMBINED = "combined"
    I_FIRST = "i_first"
    I_SECOND = "i_second"


@dataclass(frozen=True)
class MetricOptions:
    split: GameSplit = GameSplit.COMBINED
    confidence: float = 0.95
    include_fails: bool = False


def _select(games: list[GameTracker], tracker: ResultTracker, split: GameSplit) -> list[GameTracker]:
    if split is GameSplit.COMBINED:
        return games
    i_first, i_second = ResultTracker.split_games_by_starting_player(games, tracker.i)
    return i_first if split is GameSplit.I_FIRST else i_second


def _find(extractors: list[Extractor], metric: MetricName) -> Extractor | None:
    return next((extractor for extractor in extractors if extractor.name is metric), None)


def _check_grouped(trackers: list[ResultTracker]) -> None:
    first = trackers[0]
    if any(tracker.i.hash != first.i.hash or tracker.game.to_string() != first.game.to_string() for tracker in trackers):
        raise ValueError("pooling a group that does not share one game and one analysed player; group the trackers by (game, player) first")


class MetricPool:
    def __init__(self, registry: Registry | None, options: MetricOptions | None = None) -> None:
        self._registry = registry
        self._options = options or MetricOptions()
        self._suites: dict[tuple[str, str], list[Extractor]] = {}

    @property
    def options(self) -> MetricOptions:
        return self._options

    def bundle(self, trackers: list[ResultTracker], metric: MetricName) -> CIBundle | None:
        if not trackers:
            return None
        _check_grouped(trackers)

        extractor = _find(self._suite(trackers[0]), metric)
        if extractor is None:
            return None

        games = [game for tracker in trackers for game in _select([game for game in tracker.games if game is not None], tracker, self._options.split)]
        if not games:
            return None

        distribution = extractor.extract(games, trackers[0].i)
        return bundle_for_family(extractor.family, distribution, self._options.confidence) if distribution.n else None

    def _suite(self, tracker: ResultTracker) -> list[Extractor]:
        key = (tracker.game.to_string(), tracker.i.hash)
        if key not in self._suites:
            self._suites[key] = matchup_suite(tracker, self._registry, self._options.include_fails)
        return self._suites[key]


def pooled_bundle(trackers: list[ResultTracker], metric: MetricName, registry: Registry | None, options: MetricOptions | None = None) -> CIBundle | None:
    return MetricPool(registry, options).bundle(trackers, metric)
