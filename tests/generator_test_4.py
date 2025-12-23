from modules import PairwiseMatrixGenerator

# тест подгонки согласованности (CR)

for target in [0.05, 0.10, 0.20, 0.35, 0.50]:
    gen = (
        PairwiseMatrixGenerator()
        .set_seed(42)
        .set_n(5)
        .set_target_cr(target)
        .set_round_digits(3)
    )

    A = gen.generate_pairwise(PairwiseMatrixGenerator.MODE_INCONSISTENT)

    print("\n--- target_cr ≈", target, "---")
    for row in A:
        print(row)
    print("CR =", PairwiseMatrixGenerator.consistency_ratio(A))
