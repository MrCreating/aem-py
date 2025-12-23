from modules import PairwiseMatrixGenerator

# тест согласованных матриц

gen = (
    PairwiseMatrixGenerator()
    .set_seed(42)
    .set_n(5)
    .set_round_digits(2)
)

A = gen.generate_pairwise(PairwiseMatrixGenerator.MODE_CONSISTENT)

print("Матрица:")
for row in A:
    print(row)

print("CR =", PairwiseMatrixGenerator.consistency_ratio(A))
