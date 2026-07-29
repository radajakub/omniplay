from collections.abc import Callable

from omniplay.utils.enums import ExtendedEnum
from omniplay.utils.text import number_to_char_upper


class GridAxisLabel(ExtendedEnum):
    NUMBERS = "numbers"
    LETTERS = "letters"
    NONE = "none"


class GridAxisDirection(ExtendedEnum):
    FORWARD = "forward"
    REVERSED = "reversed"


def grid_to_positions(grid: list[list[str]], i_symbol: str, o_symbol: str, label: Callable[[int, int], str]) -> tuple[list[str], list[str]]:
    positions: dict[str, list[str]] = {i_symbol: [], o_symbol: []}
    for r, row in enumerate(grid, start=1):
        for c, symbol in enumerate(row, start=1):
            if symbol in positions:
                positions[symbol].append(label(r, c))
    return positions[i_symbol], positions[o_symbol]


class GridPrinter:
    def __init__(
        self,
        row_header: GridAxisLabel = GridAxisLabel.NONE,
        row_direction: GridAxisDirection = GridAxisDirection.FORWARD,
        col_header: GridAxisLabel = GridAxisLabel.NONE,
        col_direction: GridAxisDirection = GridAxisDirection.FORWARD,
    ) -> None:
        self.row_header = row_header
        self.row_direction = row_direction
        self.col_header = col_header
        self.col_direction = col_direction

    def _apply_direction(self, values: list[str], direction: GridAxisDirection) -> list[str]:
        match direction:
            case GridAxisDirection.FORWARD:
                return values
            case GridAxisDirection.REVERSED:
                return values[::-1]

    def _build_headers(self, count: int, header_type: GridAxisLabel, header_direction: GridAxisDirection) -> list[str] | None:
        match header_type:
            case GridAxisLabel.NUMBERS:
                return self._apply_direction([str(i + 1) for i in range(count)], header_direction)
            case GridAxisLabel.LETTERS:
                return self._apply_direction([number_to_char_upper(i) for i in range(count)], header_direction)
            case GridAxisLabel.NONE:
                return None

    def __call__(self, grid: list[list[str]]) -> str:
        row_headers = self._build_headers(len(grid), self.row_header, self.row_direction)
        col_headers = self._build_headers(len(grid[0]), self.col_header, self.col_direction)
        return self.print_grid(grid, row_headers, col_headers)

    def print_grid(self, grid: list[list[str]], row_labels: list[str] | None = None, col_labels: list[str] | None = None) -> str:
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

        if col_labels:
            lines.append("   " + " ".join(f" {label:^{cell_width}} " for label in col_labels))

        border_segment = "-" * (cell_width + 2)
        top_border = "  +" + "+".join(border_segment for _ in range(num_cols)) + "+"
        lines.append(top_border)

        for row_idx, row in enumerate(grid):
            if row_labels and row_idx < len(row_labels):
                row_str = f"{row_labels[row_idx]} |" + "|".join(f" {cell:^{cell_width}} " for cell in row) + "|" + f" {row_labels[row_idx]}"
            else:
                row_str = "  |" + "|".join(f" {cell:^{cell_width}} " for cell in row) + "|"
            lines.append(row_str)

            if row_idx < num_rows - 1:
                lines.append("  +" + "+".join(border_segment for _ in range(num_cols)) + "+")

        lines.append("  +" + "+".join(border_segment for _ in range(num_cols)) + "+")

        if col_labels:
            lines.append("   " + " ".join(f" {label:^{cell_width}} " for label in col_labels))

        return "\n".join(lines)
