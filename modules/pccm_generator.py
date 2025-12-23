# Модуль генерации МПС разного уровня согласованности для синтетических тестов
# основной проект aem-py (Азаров И. И, https://github.com/MrCreating/aem-py), но можно переиспользовать ьв других

from __future__ import annotations

import math
import random
from typing import List, Optional, Dict

class PairwiseMatrixGenerator:
    """
        Генератор матриц попарных сравнений (МПС) в рамках метода анализа иерархий (AHP)
    """

    # максимально возможно согласованная
    MODE_CONSISTENT = "consistent"
    # максимально возможно несогласованная
    MODE_INCONSISTENT = "inconsistent"
    # чистый рандом приведенный к Саати
    MODE_RANDOM_SAATY = "random_saaty"

    _RI: Dict[int, float] = {
        1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
        6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
    }

    _SAATY_SCALE = (1, 2, 3, 4, 5, 6, 7, 8, 9)

    # основной генератор
    def __init__(self):
        self._seed: Optional[int] = None
        self._rng = random.Random()
        self._n = 5
        self._sigma = 0.0
        self._target_cr: Optional[float] = None
        self._quantize_flag = False
        self._clip_flag = True
        self._round_digits: Optional[int] = None

    def set_round_digits(self, digits: Optional[int]):
        """
            Ограничивает количество знаков после запятой у элементов МПС

            Используется для повышения читаемости матриц и
            упрощения последующего анализа результатов

            Параметры:
                digits (int | None): число знаков после запятой
                    Если None, округление не применяется
        """
        if digits is not None and digits < 0:
            raise ValueError("digits must be >= 0 or None")

        self._round_digits = digits
        return self

    def set_seed(self, seed: Optional[int]):
        """
            Устанавливает зерно генератора случайных чисел

            Используется для воспроизводимости экспериментов
            При одинаковом значении seed генератор будет создавать идентичные матрицы

            Параметры:
                seed (int | None): значение зерна генератора.
                    Если None, используется случайная инициализация
        """
        self._seed = seed
        self._rng = random.Random(seed)
        return self

    def set_n(self, n: int):
        """
            Устанавливает размерность генерируемых матриц

            Параметры:
                n (int): число альтернатив (размер матрицы n×n)
        """
        self._n = n
        return self

    def set_sigma(self, sigma: float):
        """
            Устанавливает уровень мультипликативного шума

            Параметр sigma управляет интенсивностью лог. нормального
            шума, применяемого к элементам матрицы при генерации
            несогласованных МПС

            Параметры:
                sigma (float): стандартное отклонение шума (sigma >= 0)
        """
        self._sigma = sigma
        return self

    def set_target_cr(self, cr: Optional[float]):
        """
            Задаёт целевое значение индекса согласованности CR

            Если значение задано, генератор автоматически подбирает
            уровень шума таким образом, чтобы согласованность
            результирующей матрицы была близка к указанному значению

            Параметры:
                cr (float | None): целевое значение CR [0, 1]
                    Если None, целевая подгонка не выполняется
        """
        self._target_cr = cr
        return self

    def quantize_to_saaty(self, enabled: bool = True):
        """
            Включает или отключает квантование значений матрицы
            к дискретной шкале Саати (1–9 и обратные значения)

            При включении все элементы матрицы приводятся
            к ближайшему допустимому значению шкалы Саати

            Параметры:
                enabled (bool): флаг включения квантования
        """
        self._quantize_flag = enabled
        return self

    def generate_pairwise(self, kind: str = MODE_CONSISTENT) -> List[List[float]]:
        """
            Генерирует матрицу попарных сравнений заданного типа

            Допустимые режимы:
                - MODE_CONSISTENT
                - MODE_INCONSISTENT
                - MODE_RANDOM_SAATY
            (см комменты к константам)
        """
        if kind == self.MODE_CONSISTENT:
            return self._generate_consistent()

        if kind == self.MODE_INCONSISTENT:
            return self._generate_inconsistent()

        if kind == self.MODE_RANDOM_SAATY:
            return self._generate_random()

        raise ValueError(
            f"Неизвестный режим генерации: {kind}. "
        )

    @staticmethod
    def consistency_ratio(a: List[List[float]]) -> float:
        """
            Вычисляет индекс согласованности CR для заданной МПС

            Расчёт основан на классической формуле Саати с использованием максимального собственного значения
            матрицы и табличных значений случайного индекса (RI)

            Параметры:
                a (list[list[float]]): матрица попарных сравнений

            Возвращает:
                float — значение CR >= 0
        """
        n = len(a)
        if n < 3:
            return 0.0
        ri = PairwiseMatrixGenerator._RI.get(n, 0.0)
        if ri == 0:
            return 0.0
        w = PairwiseMatrixGenerator._power_method(a)
        lam = PairwiseMatrixGenerator._lambda_max(a, w)
        ci = (lam - n) / (n - 1)
        return max(0.0, ci / ri)

    # всякие мат.хелперы, не стал выносить из класса во избежание конфликтов если будет в других проектах.
    @staticmethod
    def _zeros(n: int) -> List[List[float]]:
        return [[0.0 for _ in range(n)] for __ in range(n)]

    @staticmethod
    def _identity(n: int) -> List[List[float]]:
        m = PairwiseMatrixGenerator._zeros(n)
        for i in range(n):
            m[i][i] = 1.0
        return m

    @staticmethod
    def _copy(a: List[List[float]]) -> List[List[float]]:
        return [row[:] for row in a]

    @staticmethod
    def _enforce_reciprocal(a: List[List[float]]) -> None:
        n = len(a)
        for i in range(n):
            a[i][i] = 1.0
            for j in range(i + 1, n):
                x = max(a[i][j], 1e-12)
                a[i][j] = x
                a[j][i] = 1.0 / x

    @staticmethod
    def _normalize(v: List[float]) -> List[float]:
        s = sum(v)
        if s <= 0:
            return [1.0 / len(v)] * len(v)
        return [x / s for x in v]

    @staticmethod
    def _mat_vec(a: List[List[float]], v: List[float]) -> List[float]:
        n = len(a)
        out = [0.0] * n
        for i in range(n):
            out[i] = sum(a[i][j] * v[j] for j in range(n))
        return out

    @staticmethod
    def _power_method(a: List[List[float]], iters: int = 200, tol: float = 1e-12) -> List[float]:
        n = len(a)
        v = [1.0 / n] * n
        for _ in range(iters):
            v2 = PairwiseMatrixGenerator._normalize(
                PairwiseMatrixGenerator._mat_vec(a, v)
            )
            if sum(abs(v2[i] - v[i]) for i in range(n)) < tol:
                return v2
            v = v2
        return v

    @staticmethod
    def _lambda_max(a: List[List[float]], w: List[float]) -> float:
        aw = PairwiseMatrixGenerator._mat_vec(a, w)
        ratios = [(aw[i] / w[i]) for i in range(len(w)) if w[i] > 0]
        return sum(ratios) / len(ratios)

    @staticmethod
    def _clip(x: float) -> float:
        return min(9.0, max(1.0 / 9.0, x))

    @staticmethod
    def _quantize(x: float) -> float:
        scale = PairwiseMatrixGenerator._SAATY_SCALE
        candidates = list(scale) + [1 / s for s in scale]
        return min(candidates, key=lambda c: abs(math.log(x) - math.log(c)))

    @staticmethod
    def _round(x: float, digits: Optional[int]) -> float:
        if digits is None:
            return x
        return round(x, digits)


    # САМА ГЕНЕРАЦИЯ
    def _apply_noise(self, a: List[List[float]], sigma: float) -> List[List[float]]:
        out = self._copy(a)
        for i in range(self._n):
            for j in range(i + 1, self._n):
                x = out[i][j] * math.exp(self._rng.gauss(0, sigma))
                if self._clip_flag:
                    x = self._clip(x)
                if self._quantize_flag:
                    x = self._quantize(x)
                out[i][j] = self._round(x, self._round_digits)
        self._enforce_reciprocal(out)
        return out

    def _generate_consistent(self) -> List[List[float]]:
        w = [math.exp(self._rng.uniform(-1, 1)) for _ in range(self._n)]
        w = self._normalize(w)
        a = self._zeros(self._n)
        for i in range(self._n):
            for j in range(self._n):
                a[i][j] = self._round(w[i] / w[j], self._round_digits)
        self._enforce_reciprocal(a)
        return a

    def _generate_random(self) -> List[List[float]]:
        a = self._identity(self._n)
        for i in range(self._n):
            for j in range(i + 1, self._n):
                val = self._rng.choice(self._SAATY_SCALE)
                a[i][j] = val if self._rng.random() < 0.5 else 1 / val
                a[i][j] = self._round(a[i][j], self._round_digits)
        self._enforce_reciprocal(a)
        return a

    def _generate_inconsistent(self) -> List[List[float]]:
        base = self._generate_consistent()
        if self._target_cr is None:
            return self._apply_noise(base, self._sigma)

        lo, hi = 0.0, 2.5
        best = base
        for _ in range(20):
            mid = (lo + hi) / 2
            self.set_seed(self._seed)
            cand = self._apply_noise(base, mid)
            cr = self.consistency_ratio(cand)
            best = cand
            if abs(cr - self._target_cr) < 0.03:
                break
            if cr < self._target_cr:
                lo = mid
            else:
                hi = mid
        return best