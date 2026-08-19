from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

from matplotlib.axes import Axes
from matplotlib.ticker import FixedLocator, MaxNLocator, MultipleLocator

Which = Literal["x", "y"]


@runtime_checkable
class TickSpec(Protocol):
    def apply(self, ax: Axes, which: Which) -> None: ...


@dataclass(frozen=True)
class CategoryTicks:
    labels: tuple[str, ...]
    positions: tuple[float, ...] | None = None

    def apply(self, ax: Axes, which: Which) -> None:
        positions = self.positions if self.positions is not None else tuple(range(len(self.labels)))
        if len(positions) != len(self.labels):
            raise ValueError(f"{len(positions)} tick positions for {len(self.labels)} labels")
        axis = ax.xaxis if which == "x" else ax.yaxis
        axis.set_major_locator(FixedLocator(list(positions)))
        axis.set_ticklabels(list(self.labels))


@dataclass(frozen=True)
class StepTicks:
    step: float

    def apply(self, ax: Axes, which: Which) -> None:
        (ax.xaxis if which == "x" else ax.yaxis).set_major_locator(MultipleLocator(self.step))


@dataclass(frozen=True)
class MaxTicks:
    # MaxNLocator counts intervals, so this yields up to count + 1 ticks
    count: int

    def apply(self, ax: Axes, which: Which) -> None:
        (ax.xaxis if which == "x" else ax.yaxis).set_major_locator(MaxNLocator(nbins=self.count))
