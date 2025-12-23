from modules import PairwiseMatrixGenerator

# тест рандом на Саати шкале (без сида)

gen = (
    PairwiseMatrixGenerator()
    .set_n(5)
    .set_round_digits(3)
)

A = gen.generate_pairwise(PairwiseMatrixGenerator.MODE_RANDOM_SAATY)

print("Матрица:")
for row in A:
    print(row)
print("CR =", PairwiseMatrixGenerator.consistency_ratio(A))
