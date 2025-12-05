from __future__ import annotations

from typing import List, Optional, Sequence


class MatrixPrinter:
    def __init__(
        self,
        float_format: str = ".4f",
        padding: int = 1,
        use_ascii_borders: bool = True,
    ) -> None:
        """
        float_format: спецификатор формата для чисел, например '.4f', '.3f', 'g'
        padding: количество пробелов слева и справа в каждой ячейке
        use_ascii_borders: использовать ли ASCII-рамку (|, -, +)
        """
        self._float_format = float_format
        self._padding = padding
        self._use_ascii_borders = use_ascii_borders

    def format_matrix(
        self,
        matrix: Sequence[Sequence[float]],
        row_labels: Optional[Sequence[str]] = None,
        col_labels: Optional[Sequence[str]] = None,
        title: Optional[str] = None,
    ) -> str:
        global header_border
        self._validate_matrix(matrix, row_labels, col_labels)

        rows_count = len(matrix)
        cols_count = len(matrix[0]) if rows_count > 0 else 0

        cell_strings: List[List[str]] = []
        for i in range(rows_count):
            row_strs: List[str] = []
            for j in range(cols_count):
                value = matrix[i][j]
                row_strs.append(self._format_number(value))
            cell_strings.append(row_strs)

        col_headers = list(col_labels) if col_labels is not None else []
        row_headers = list(row_labels) if row_labels is not None else []

        col_widths = self._compute_column_widths(
            cell_strings=cell_strings,
            col_headers=col_headers,
            row_headers=row_headers,
        )

        lines: List[str] = []

        if title:
            lines.append(title)

        if self._use_ascii_borders:
            header_border = self._build_horizontal_border(col_widths)
            lines.append(header_border)

        if col_headers:
            header_line = self._build_header_line(
                col_headers=col_headers,
                col_widths=col_widths,
                has_row_header=bool(row_headers),
            )
            lines.append(header_line)
            if self._use_ascii_borders:
                lines.append(header_border)

        for i in range(rows_count):
            row_line = self._build_data_line(
                row_index=i,
                cell_strings=cell_strings,
                row_headers=row_headers,
                col_widths=col_widths,
            )
            lines.append(row_line)

        if self._use_ascii_borders:
            lines.append(header_border)

        return "\n".join(lines)

    def print_matrix(
        self,
        matrix: Sequence[Sequence[float]],
        row_labels: Optional[Sequence[str]] = None,
        col_labels: Optional[Sequence[str]] = None,
        title: Optional[str] = None,
    ) -> None:
        table_str = self.format_matrix(
            matrix=matrix,
            row_labels=row_labels,
            col_labels=col_labels,
            title=title,
        )
        print(table_str)

    @staticmethod
    def _validate_matrix(
        matrix: Sequence[Sequence[float]],
        row_labels: Optional[Sequence[str]],
        col_labels: Optional[Sequence[str]],
    ) -> None:
        if not matrix:
            return

        rows_count = len(matrix)
        cols_count = len(matrix[0])

        for row in matrix:
            if len(row) != cols_count:
                raise ValueError("Матрица должна быть прямоугольной.")

        if row_labels is not None and len(row_labels) != rows_count:
            raise ValueError(
                f"Число подписей строк ({len(row_labels)}) не совпадает "
                f"с числом строк матрицы ({rows_count})."
            )

        if col_labels is not None and len(col_labels) != cols_count:
            raise ValueError(
                f"Число подписей столбцов ({len(col_labels)}) не совпадает "
                f"с числом столбцов матрицы ({cols_count})."
            )

    def _format_number(self, value: float) -> str:
        try:
            return format(value, self._float_format)
        except (ValueError, TypeError):
            return str(value)

    def _compute_column_widths(
        self,
        cell_strings: List[List[str]],
        col_headers: List[str],
        row_headers: List[str],
    ) -> List[int]:
        rows_count = len(cell_strings)
        cols_count = len(cell_strings[0]) if rows_count > 0 else 0

        col_widths: List[int] = [0] * cols_count

        for j in range(cols_count):
            max_width = 0

            if col_headers:
                max_width = max(max_width, len(col_headers[j]))

            for i in range(rows_count):
                max_width = max(max_width, len(cell_strings[i][j]))

            col_widths[j] = max_width + 2 * self._padding

        if row_headers:
            max_row_label_len = max(len(label) for label in row_headers)
            row_header_width = max_row_label_len + 2 * self._padding
            col_widths = [row_header_width] + col_widths

        return col_widths

    def _build_horizontal_border(
        self,
        col_widths: List[int],
    ) -> str:
        if not self._use_ascii_borders:
            return ""

        parts: List[str] = ["+"]

        for width in col_widths:
            parts.append("-" * width)
            parts.append("+")

        return "".join(parts)

    def _build_header_line(
        self,
        col_headers: List[str],
        col_widths: List[int],
        has_row_header: bool,
    ) -> str:
        cells: List[str] = []

        col_index_offset = 0
        if has_row_header:
            width = col_widths[0]
            cells.append(self._format_cell("", width))
            col_index_offset = 1

        for j, header in enumerate(col_headers):
            width = col_widths[col_index_offset + j]
            cells.append(self._format_cell(header, width))

        if self._use_ascii_borders:
            return "|" + "|".join(cells) + "|"

        return " ".join(cells)

    def _build_data_line(
        self,
        row_index: int,
        cell_strings: List[List[str]],
        row_headers: List[str],
        col_widths: List[int],
    ) -> str:
        row_cells: List[str] = []

        has_row_header = bool(row_headers)
        col_index_offset = 0

        if has_row_header:
            label = row_headers[row_index]
            width = col_widths[0]
            row_cells.append(self._format_cell(label, width))
            col_index_offset = 1

        row_data = cell_strings[row_index]
        for j, cell in enumerate(row_data):
            width = col_widths[col_index_offset + j]
            row_cells.append(self._format_cell(cell, width))

        if self._use_ascii_borders:
            return "|" + "|".join(row_cells) + "|"

        return " ".join(row_cells)

    def _format_cell(self, content: str, width: int) -> str:
        raw = content

        inner_width = max(0, width - 2 * self._padding)

        if self._is_number_like(raw):
            aligned = raw.rjust(inner_width)
        else:
            aligned = raw.ljust(inner_width)

        return " " * self._padding + aligned + " " * self._padding

    @staticmethod
    def _is_number_like(text: str) -> bool:
        if not text:
            return False
        try:
            float(text.replace(",", "."))
            return True
        except ValueError:
            return False
