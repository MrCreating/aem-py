from modules import Context, AHP
from utils import Validator


def main() -> None:
    context = Context.from_json_file("examples/graduation_defense.json")

    validator = Validator(context)
    percent_ok = validator.validate(strict=True)
    print(f"Валидность контекста: {percent_ok}%")
    if validator.get_errors():
        print("Ошибки валидации:")
        for err in validator.get_errors():
            print(" -", err)

    ahp = AHP(context)
    result = ahp.solve()

    print("\nВЕСА КРИТЕРИЕВ:")
    for crit_id, w in result.criteria_weights.items():
        print(f"  {crit_id}: {w:.4f}")
    print(
        f"Согласованность критериев: OS={result.criteria_consistency_os:.4f}, "
        f"{result.criteria_consistency_percent:.2f}%"
    )

    print("\nВЕСА АЛЬТЕРНАТИВ ПО КРИТЕРИЯМ:")
    for c_id, alt_weights in result.alt_weights_by_criterion.items():
        print(f"  Критерий {c_id}:")
        for alt_id, w in alt_weights.items():
            print(f"    {alt_id}: {w:.4f}")
        os = result.alt_consistency_os_by_criterion.get(c_id, 0.0)
        osp = result.alt_consistency_percent_by_criterion.get(c_id, 0.0)
        print(f"    OS={os:.4f}, {osp:.2f}%")

    print("\nИТОГОВЫЕ ВЕСА АЛЬТЕРНАТИВ:")
    for alt_id, w in result.global_alt_weights.items():
        print(f"  {alt_id}: {w:.4f}")


if __name__ == "__main__":
    main()