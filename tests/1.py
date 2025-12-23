from modules import PairwiseMatrixGenerator

gen = (
    PairwiseMatrixGenerator()
    .set_seed(42)
    .set_n(5)
)

A = gen.generate_pairwise(PairwiseMatrixGenerator.MODE_CONSISTENT)

print("Матрица:")
for row in A:
    print(row)

print("CR =", PairwiseMatrixGenerator.consistency_ratio(A))