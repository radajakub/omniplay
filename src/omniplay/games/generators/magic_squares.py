from __future__ import annotations

import numpy as np

from omniplay.games.generators.generator import InstanceGenerator


class MagicSquare:
    def __init__(self, square: np.ndarray) -> None:
        self.square = square
        self.magic_constant = self.is_magic()

    def is_magic(self) -> int:
        sums = []
        for i in range(3):
            sums.append(np.sum(self.square[i, :]))
        for i in range(3):
            sums.append(np.sum(self.square[:, i]))
        sums.append(np.sum(self.square.diagonal()))
        sums.append(np.sum(np.fliplr(self.square).diagonal()))
        sums = np.array(sums)
        assert np.all(sums == sums[0]), "The square is not magic"
        return sums[0]

    def __call__(self, row: int, col: int) -> int:
        return self.square[row][col]

    def __add__(self, k: int) -> MagicSquare:
        return MagicSquare(self.square + k)

    def __sub__(self, k: int) -> MagicSquare:
        return MagicSquare(self.square - k)

    def __mul__(self, k: int) -> MagicSquare:
        return MagicSquare(self.square * k)

    def rotate(self) -> MagicSquare:
        return MagicSquare(np.rot90(self.square))

    def reflect_horizontal(self) -> MagicSquare:
        return MagicSquare(np.fliplr(self.square))

    def reflect_vertical(self) -> MagicSquare:
        return MagicSquare(np.flipud(self.square))


class MagicSquareGenerator(InstanceGenerator[MagicSquare]):
    def __init__(self, sample: bool = False, magic_constant_add: int = 0) -> None:
        super().__init__(sample=sample)
        self.lo_shu = (
            MagicSquare(
                np.array(
                    [
                        [4, 9, 2],
                        [3, 5, 7],
                        [8, 1, 6],
                    ]
                )
            )
            + magic_constant_add
        )
        self.magic_constant_add = magic_constant_add
        self.all_squares = self._generate()

    def _generate(self) -> list[MagicSquare]:
        return [
            self.lo_shu,
            self.lo_shu.rotate(),
            self.lo_shu.rotate().rotate(),
            self.lo_shu.rotate().rotate().rotate(),
            self.lo_shu.reflect_horizontal(),
            self.lo_shu.reflect_vertical(),
            self.lo_shu.rotate().reflect_horizontal(),
            self.lo_shu.rotate().reflect_vertical(),
        ]

    def get_normal(self) -> MagicSquare:
        return self.lo_shu

    def sample(self) -> MagicSquare:
        idx = self.generator.integers(0, len(self.all_squares))
        return self.all_squares[idx]
