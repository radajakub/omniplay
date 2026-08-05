from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from plybench.analysis.recognition import recognizable
from plybench.analysis.statistics.bundle import CIBundle
from plybench.analysis.statistics.comparison import GroupComparison
from plybench.analysis.stats.move_features import MoveFeature
from plybench.analysis.stats.move_metrics import DEFAULT_MOVE_METRICS, MoveMetric
from plybench.analysis.stats.moves import MoveRecord, collect_moves
from plybench.common.enums import MetricName
from plybench.configs.game_config import GameConfig
from plybench.configs.player_config import PlayerConfig
from plybench.registry import Registry
from plybench.trackers.result_tracker import ResultTracker


@dataclass(frozen=True)
class Partition:
    label: str
    moves: list[MoveRecord]


class Partitioner(ABC):
    """Splits a matchup's judged moves into named, ordered groups. The first group is the baseline every
    other group is compared against. Sees the whole move list, so median/quantile splits are possible,
    not only per-move predicates. Fully decoupled from replay — it reads only MoveRecords."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def partition(self, moves: list[MoveRecord]) -> list[Partition]:
        raise NotImplementedError


class BinaryPartitioner(Partitioner):
    """Two groups from a per-move predicate: the negative (predicate False) group is the baseline, the
    positive (True) group is compared against it, so the reported difference reads as positive-minus-
    baseline. Moves whose predicate is None are undefined for this split and dropped."""

    def __init__(self, name: str, positive_label: str, negative_label: str, predicate: Callable[[MoveRecord], bool | None]) -> None:
        super().__init__(name)
        self._positive_label = positive_label
        self._negative_label = negative_label
        self._predicate = predicate

    def partition(self, moves: list[MoveRecord]) -> list[Partition]:
        positive, negative = [], []
        for move in moves:
            verdict = self._predicate(move)
            if verdict is True:
                positive.append(move)
            elif verdict is False:
                negative.append(move)
        return [Partition(self._negative_label, negative), Partition(self._positive_label, positive)]


def by_recognition() -> BinaryPartitioner:
    return BinaryPartitioner("recognition", "recognized", "not_recognized", lambda move: move.recognized)


class QuantilePartitioner(Partitioner):
    """Bins moves by a continuous feature at its own quantiles, lowest bin first (so comparisons read as
    higher-feature minus lowest bin). Discrete features in small games often yield fewer than `n_bins`
    distinct edges, and empty bins are dropped, so the group count is a maximum rather than a promise."""

    def __init__(self, name: str, feature: MoveFeature, n_bins: int = 3) -> None:
        super().__init__(name)
        self._feature = feature
        self._n_bins = n_bins

    def partition(self, moves: list[MoveRecord]) -> list[Partition]:
        if not moves:
            return []

        values = np.array([self._feature(move) for move in moves])
        edges = np.unique(np.quantile(values, np.linspace(0.0, 1.0, self._n_bins + 1)))
        if len(edges) < 2:  # a single distinct value: one bin holding everything
            return [Partition(f"{self.name}~{edges[0]:.2f}", list(moves))]

        index = np.clip(np.searchsorted(edges, values, side="right") - 1, 0, len(edges) - 2)
        partitions = []
        for b in range(len(edges) - 1):
            members = [move for move, i in zip(moves, index, strict=True) if i == b]
            if members:
                partitions.append(Partition(f"{self.name}[{edges[b]:.2f},{edges[b + 1]:.2f}]", members))
        return partitions


@dataclass(frozen=True)
class GroupMetrics:
    label: str
    n_moves: int
    metrics: dict[MetricName, CIBundle]

    def to_dict(self) -> dict[str, Any]:
        return {"label": self.label, "n_moves": self.n_moves, "metrics": {name.value: bundle.to_dict() for name, bundle in self.metrics.items()}}


@dataclass(frozen=True)
class PartitionStats:
    """For one (game, player, opponent) cell: the analysed player's judged moves grouped by a partitioner
    and summarised per group on each move-metric, plus a between-group comparison of every non-baseline
    group against the baseline (the first group). Only defined for solvable games (needs the replay)."""

    experiment: str
    i: PlayerConfig
    o: PlayerConfig
    game: GameConfig
    partitioner: str
    n_moves: int
    groups: list[GroupMetrics]
    comparisons: dict[str, dict[MetricName, GroupComparison]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment": self.experiment,
            "i_config": self.i.to_string(),
            "o_config": self.o.to_string(),
            "game_config": self.game.to_string(),
            "partitioner": self.partitioner,
            "n_moves": self.n_moves,
            "groups": [group.to_dict() for group in self.groups],
            "comparisons": {label: {name.value: comp.to_dict() for name, comp in metrics.items()} for label, metrics in self.comparisons.items()},
        }


def _group_metrics(partition: Partition, metrics: Sequence[MoveMetric], confidence: float) -> GroupMetrics:
    return GroupMetrics(partition.label, len(partition.moves), {metric.name: metric.bundle(partition.moves, confidence) for metric in metrics})


def _comparison(baseline: Partition, group: Partition, metrics: Sequence[MoveMetric], confidence: float) -> dict[MetricName, GroupComparison]:
    return {metric.name: metric.compare(group.moves, baseline.moves, confidence) for metric in metrics}


def compute_partition_stats(
    tracker: ResultTracker,
    registry: Registry,
    partitioner: Partitioner,
    metrics: Sequence[MoveMetric] = DEFAULT_MOVE_METRICS,
    confidence: float = 0.95,
) -> PartitionStats | None:
    """Group one matchup's judged moves with `partitioner` and compute per-group move-metrics plus each
    group's comparison to the baseline. Returns None when the game is unsolvable (no replay) or produced
    no judged moves."""
    if not registry.solvable(tracker.game.key):
        return None

    moves = collect_moves(tracker, registry)
    if not moves:
        return None

    partitions = partitioner.partition(moves)
    if not partitions:  # the partitioner found nothing it could group (e.g. every move undefined for it)
        return None
    baseline = partitions[0]
    return PartitionStats(
        experiment=tracker.experiment,
        i=tracker.i,
        o=tracker.o,
        game=tracker.game,
        partitioner=partitioner.name,
        n_moves=len(moves),
        groups=[_group_metrics(partition, metrics, confidence) for partition in partitions],
        comparisons={partition.label: _comparison(baseline, partition, metrics, confidence) for partition in partitions[1:]},
    )


def compute_recognition_split(tracker: ResultTracker, registry: Registry, confidence: float = 0.95) -> PartitionStats | None:
    """Recognition split: the default move-metrics grouped by whether the reasoning trace recognised the
    underlying game. None for unrecognisable or unsolvable games (or matchups with no reasoning traces)."""
    if not recognizable(tracker.game.key):
        return None
    stats = compute_partition_stats(tracker, registry, by_recognition(), DEFAULT_MOVE_METRICS, confidence)
    # every group empty means no move carried a trace -> recognition is undefined for this matchup
    if stats is None or all(group.n_moves == 0 for group in stats.groups):
        return None
    return stats
