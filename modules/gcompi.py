from __future__ import annotations

import math
from typing import List


class GcompiCalculator:
    def __init__(self) -> None:
        pass

    @staticmethod
    def _log_sq(x: float) -> float:
        """(ln x)^2, x > 0"""
        ln = math.log(x)
        return ln * ln

    @staticmethod
    def _gcompi_single(matrix: List[List[float]], u: List[float]) -> float:
        n = len(matrix)
        if n <= 2:
            return 0.0

        denom = float((n - 1) * (n - 2))
        if denom == 0.0:
            return 0.0

        total = 0.0
        for i in range(n):
            ui = u[i]
            if ui == 0.0:
                continue
            for j in range(n):
                value = matrix[i][j] * (u[j] / ui)
                if value <= 0.0:
                    continue
                total += GcompiCalculator._log_sq(value)

        return total / denom

    @staticmethod
    def gcompi_family(
        matrices: List[List[List[float]]],
        weights: List[float],
        u: List[float],
    ) -> float:
        if not matrices:
            return 0.0

        n = len(matrices[0])
        if n <= 2:
            return 0.0

        w_sum = sum(max(w, 0.0) for w in weights)
        if w_sum == 0.0:
            w_norm = [1.0 / len(matrices)] * len(matrices)
        else:
            w_norm = [max(w, 0.0) / w_sum for w in weights]

        denom = float((n - 1) * (n - 2))
        total = 0.0

        for k, matrix in enumerate(matrices):
            alpha_k = w_norm[k]
            if alpha_k == 0.0:
                continue

            inner = 0.0
            for i in range(n):
                ui = u[i]
                if ui == 0.0:
                    continue
                for j in range(n):
                    value = matrix[i][j] * (u[j] / ui)
                    if value <= 0.0:
                        continue
                    inner += GcompiCalculator._log_sq(value)

            total += alpha_k * inner

        return total / denom
