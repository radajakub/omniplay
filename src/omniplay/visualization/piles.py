from omniplay.visualization.grid import GridPrinter


class PilePrinter:
    def __init__(self, column_label: str = "pile", fixed_height: int | None = None) -> None:
        self.grid_printer = GridPrinter()
        self.column_label = column_label
        self.fixed_height = fixed_height

    def __call__(self, piles: list[int]) -> str:
        if not piles:
            return ""

        max_height = self.fixed_height if self.fixed_height is not None else max(piles) + 1
        num_piles = len(piles)

        col_labels = [f"{self.column_label}:{i + 1}" for i in range(num_piles)]

        grid = []
        row_labels = []
        for height in range(1, max_height + 1):
            row_labels.append(str(height))
            grid.append(["●" if piles[pile_idx] >= height else " " for pile_idx in range(num_piles)])

        row_labels = row_labels[::-1]
        grid = grid[::-1]

        return self.grid_printer.print_grid(grid, row_labels, col_labels)
