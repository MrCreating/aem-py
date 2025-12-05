from typing import Dict, List

class Math:
    def __init__(self) -> None:
        self._random_index: Dict[int, float] = {
            1: 0.0,
            2: 0.0,
            3: 0.58,
            4: 0.90,
            5: 1.12,
            6: 1.24,
            7: 1.32,
            8: 1.41,
            9: 1.45,
            10: 1.49,
        }

    @staticmethod
    def compute_priority_vector(matrix: List[List[float]]) -> List[float]:
        """
        Считаем вектора приоритетов для МПС
        :param matrix:
        :return:
        """
        n = len(matrix)

        geom_means: List[float] = []
        for i in range(n):
            product = 1.0
            for j in range(n):
                product *= matrix[i][j]
            geom_means.append(product ** (1.0 / n))

        total = sum(geom_means)
        if total == 0:
            return [1.0 / n] * n

        return [g / total for g in geom_means]

    @staticmethod
    def compute_lambda_max(matrix: List[List[float]], weights: List[float]) -> float:
        """
        :param matrix:
        :param weights:
        :return:
        """
        n = len(matrix)
        aw: List[float] = [0.0] * n
        for i in range(n):
            s = 0.0
            for j in range(n):
                s += matrix[i][j] * weights[j]
            aw[i] = s

        ratios: List[float] = []
        for i in range(n):
            if weights[i] == 0:
                continue
            ratios.append(aw[i] / weights[i])

        if not ratios:
            return float(n)

        return sum(ratios) / len(ratios)

    def compute_relative_consistency(self, matrix: List[List[float]]) -> float:
        """
        Считаем относительную согласованность
        :param matrix:
        :return:
        """
        n = len(matrix)
        if n <= 2:
            return 0.0

        weights = self.compute_priority_vector(matrix)
        lambda_max = self.compute_lambda_max(matrix, weights)
        ci = (lambda_max - n) / (n - 1)

        ri = self._random_index.get(n, 0.0)
        if ri == 0.0:
            return 0.0

        os = ci / ri
        if os < 0.0:
            os = 0.0
        return os

    @staticmethod
    def consistency_to_percent(relative_consistency: float) -> float:
        percent = (1.0 - relative_consistency) * 100.0
        if percent < 0.0:
            percent = 0.0
        if percent > 100.0:
            percent = 100.0
        return percent