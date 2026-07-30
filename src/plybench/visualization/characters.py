class CharacterPrinter:
    def __init__(self, fixed_width: int | None = None) -> None:
        self.fixed_width = fixed_width

    def __call__(self, names: list[str], positions: list[int]) -> str:
        if not names or not positions or len(names) != len(positions):
            return ""

        width = self.fixed_width if self.fixed_width is not None else max(positions) + 1

        col_labels = [str(i) for i in range(1, width)] + ["end"]

        max_name_width = max(len(name) for name in names) if names else 0
        row_labels = [name.rjust(max_name_width) for name in names]

        grid = []
        for char_idx in range(len(names)):
            position = positions[char_idx]
            row = ["●" if position == col_idx else " " for col_idx in range(1, width + 1)]
            grid.append(row)

        return self._print_grid_with_aligned_separators(grid, row_labels, col_labels, max_name_width)

    def _print_grid_with_aligned_separators(self, grid: list[list[str]], row_labels: list[str], col_labels: list[str], row_label_width: int) -> str:
        num_rows = len(grid)
        num_cols = len(grid[0])

        lines: list[str] = []

        cell_width = 3
        if col_labels:
            cell_width = max(cell_width, max(len(label) for label in col_labels))
        if row_labels:
            cell_width = max(cell_width, max(len(label) for label in row_labels))
        for row in grid:
            for cell in row:
                cell_width = max(cell_width, len(cell))

        separator_padding = " " * (row_label_width + 1)

        if col_labels:
            lines.append(separator_padding + " ".join(f" {label:^{cell_width}} " for label in col_labels))

        border_segment = "-" * (cell_width + 2)
        lines.append(separator_padding + "+" + "+".join(border_segment for _ in range(num_cols)) + "+")

        for row_idx, row in enumerate(grid):
            if row_labels and row_idx < len(row_labels):
                row_str = f"{row_labels[row_idx]} |" + "|".join(f" {cell:^{cell_width}} " for cell in row) + "|" + f" {row_labels[row_idx]}"
            else:
                row_str = separator_padding + "|" + "|".join(f" {cell:^{cell_width}} " for cell in row) + "|"
            lines.append(row_str)

            if row_idx < num_rows - 1:
                lines.append(separator_padding + "+" + "+".join(border_segment for _ in range(num_cols)) + "+")

        lines.append(separator_padding + "+" + "+".join(border_segment for _ in range(num_cols)) + "+")

        if col_labels:
            lines.append(separator_padding + " ".join(f" {label:^{cell_width}} " for label in col_labels))

        return "\n".join(lines)
