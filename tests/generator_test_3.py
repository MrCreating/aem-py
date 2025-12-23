from modules import PairwiseMatrixGenerator

# тест шума

for sigma in [0.05, 0.15, 0.30, 0.60, 1.00]:
    gen = (
        PairwiseMatrixGenerator()
        .set_seed(42)
        .set_n(5)
        .set_sigma(sigma)
        .set_round_digits(2)
    )

    A = gen.generate_pairwise(PairwiseMatrixGenerator.MODE_INCONSISTENT)

    print("\n--- sigma =", sigma, "---")
    for row in A:
        print(row)
    print("CR =", PairwiseMatrixGenerator.consistency_ratio(A))
