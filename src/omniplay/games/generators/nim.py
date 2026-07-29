from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from functools import reduce
from operator import ixor
from typing import Literal

from omniplay.games.generators.generator import InstanceGenerator


class NimInstance:
    def __init__(self, pile_sizes: list[int], max_pile_size: int) -> None:
        self.pile_sizes = pile_sizes
        self.max_pile_size = max_pile_size

    def inverse(self) -> NimInstance:
        return NimInstance([self.max_pile_size - pile for pile in self.pile_sizes], self.max_pile_size)

    def __str__(self) -> str:
        return f"NimInstance(pile_sizes={self.pile_sizes})"

    def __repr__(self) -> str:
        return self.__str__()


class NimGenerator(InstanceGenerator[NimInstance]):
    def __init__(
        self,
        inverse: bool = False,
        sample: bool = False,
        num_piles: int = 4,
        max_pile_size: int = 8,
        pile_sum: int = 16,
        nim_start: Literal["winning", "losing"] = "winning",
        allow_zero: bool = True,
    ) -> None:
        super().__init__(sample=sample)
        self.default = NimInstance([1, 3, 5, 7], max_pile_size)

        self.inverse = inverse
        self.num_piles = num_piles
        self.max_pile_size = max_pile_size
        self.pile_sum = pile_sum
        self.nim_start = nim_start
        self.allow_zero = allow_zero

        self.low, self.high = self._normal_interval() if not self.inverse else self._inverse_interval()

    def _normal_interval(self) -> tuple[int, int]:
        return 1, self.max_pile_size

    def _inverse_interval(self) -> tuple[int, int]:
        if self.allow_zero:
            return 0, self.max_pile_size - 1
        return 1, self.max_pile_size - 1

    def _generate_piles(self) -> Iterable[tuple[int, ...]]:
        stack: deque[tuple[list[int], int]] = deque([([], 0)])
        while len(stack) > 0:
            current_list, current_sum = stack.pop()

            if len(current_list) == self.num_piles:
                if current_sum == self.pile_sum:
                    if self.nim_start == "winning" and self._is_winning(current_list):
                        yield tuple(current_list)
                    elif self.nim_start == "losing" and not self._is_winning(current_list):
                        yield tuple(current_list)
                continue

            remaining = self.num_piles - len(current_list)
            remaining_sum = self.pile_sum - current_sum

            if remaining_sum < self.low * remaining or remaining_sum > self.high * remaining:
                continue

            for next_num in range(self.high, self.low - 1, -1):
                if current_sum + next_num <= self.pile_sum:
                    stack.append((current_list + [next_num], current_sum + next_num))

    def _is_winning(self, piles: list[int]) -> bool:
        nim_sum = reduce(ixor, piles)
        # differs in non-misere variants of Nim
        if all(pile <= 1 for pile in piles):
            return sum(1 for pile in piles if pile > 0) % 2 == 0
        return nim_sum != 0

    def get_normal(self) -> NimInstance:
        return self.default

    def sample(self) -> NimInstance:
        all_piles = list(self._generate_piles())
        sample_idx = self.generator.integers(0, len(all_piles))
        return NimInstance(list(all_piles[sample_idx]), self.max_pile_size)
