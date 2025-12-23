from modules import PairwiseMatrixGenerator

# тест размерности

gen = (
    PairwiseMatrixGenerator()
    .set_seed(42)
    .set_n(9)
    .set_target_cr(0.25)
    .set_round_digits(2)
)

A = gen.generate_pairwise(PairwiseMatrixGenerator.MODE_INCONSISTENT)

print("Матрица:")
for row in A:
    print(row)
print("CR =", PairwiseMatrixGenerator.consistency_ratio(A))
