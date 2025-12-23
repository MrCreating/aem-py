from modules import PairwiseMatrixGenerator

# Тест несогласованной матрицы (проверка, что работает - не более)

gen = (
    PairwiseMatrixGenerator()
    .set_seed(42)
    .set_target_cr(0)
    .set_n(5)
    .set_round_digits(3)
)

A = gen.generate_pairwise(PairwiseMatrixGenerator.MODE_INCONSISTENT)

print("Матрица:")
for row in A:
    print(row)

print("CR =", PairwiseMatrixGenerator.consistency_ratio(A))