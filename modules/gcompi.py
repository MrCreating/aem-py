from __future__ import annotations

import math
from typing import Dict, List


class GcompiCalculator:
    """
    Вычисление геометрического индекса совместимости GCOMPI в локальном AHP-GDM контексте
    """

    def __init__(self) -> None:
        pass

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
            for j in range(n):
                value = matrix[i][j] * (u[j] / u[i])
                if value <= 0.0:
                    continue

                log_val = math.log(value, 2.0)
                total += log_val * log_val

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
                for j in range(n):
                    value = matrix[i][j] * (u[j] / u[i])
                    if value <= 0.0:
                        continue
                    log_val = math.log(value, 2.0)
                    inner += log_val * log_val

            total += alpha_k * inner

        return total / denom
