from __future__ import annotations

from typing import Optional

from modules import Context, AHP, AemCom
from utils import Validator
from console.utils import MatrixPrinter

import os

class MainMenu:
    def __init__(self) -> None:
        self._context: Optional[Context] = None
        self._matrix_printer = MatrixPrinter(float_format=".4f", padding=1)

    @staticmethod
    def _safe_input(prompt: str) -> Optional[str]:
        try:
            return input(prompt)
        except KeyboardInterrupt:
            return "0"

    def run(self, args = None) -> None:
        while True:
            self._print_header()
            self._print_status()
            self._print_menu()

            choice = self._safe_input("Ваш выбор: ")

            if choice == "0":
                print("Выход из программы")
                return
            elif choice == "1":
                self._action_select_context(args)
            elif choice == "2":
                self._action_close_context()
            elif choice == "3":
                self._action_calculate_ahp()
            elif choice == "4":
                self._action_calculate_aemcom()
            else:
                print("Неизвестная команда. Попробуйте ещё раз.")
                self._wait_for_enter()

    @staticmethod
    def _print_header() -> None:
        print("=" * 60)
        print("  AHP / AEM-COM")
        print("=" * 60)

    def _print_status(self) -> None:
        if self._context is None:
            print("Текущий контекст: [НЕ ЗАГРУЖЕН]")
        else:
            gm = self._context.group_model
            print(f"Текущий контекст: {gm.problem.id} — {gm.problem.name}")
        print("-" * 60)

    @staticmethod
    def _print_menu() -> None:
        print("Доступные действия:")
        print("  1) Выбрать / загрузить контекст (JSON-файл)")
        print("  2) Закрыть текущий контекст")
        print("  3) Рассчитать AHP")
        print("  4) Рассчитать AEM-COM")
        print("  0) Выход")
        print("-" * 60)

    @staticmethod
    def _wait_for_enter() -> None:
        input("\nНажмите Enter, чтобы продолжить...")

    def _action_select_context(self, args) -> None:
        path = input("Введите путь к JSON-файлу с задачей AHP: ").strip()
        if not path:
            print("Путь не указан, операция отменена.")
            self._wait_for_enter()
            return

        self.load_context_from_file(path, wait_after=True, output_path=args.output)

    def load_context_from_file(self, path: str, *, output_path: Optional[str], wait_after: bool = False) -> bool:
        try:
            context = Context.from_json_file(path, result_save_path=output_path)
        except Exception as e:
            print(f"Ошибка при загрузке контекста: {e}")
            if wait_after:
                self._wait_for_enter()
            return False

        self._context = context
        gm = context.group_model
        print(f"Контекст был загружен из файла {os.path.basename(path)}")
        print(f"Контекст: {gm.problem.id} — {gm.problem.name}")
        print(f"Цель: {gm.problem.goal}")
        if context.result_save_path:
            print(f"Сохранение результатов будет выполнено в папку: {context.result_save_path}")

        if wait_after:
            self._wait_for_enter()
        return True

    def _action_close_context(self) -> None:
        if self._context is None:
            print("Контекст не загружен, закрывать нечего")
        else:
            gm = self._context.group_model
            print(f"Контекст '{gm.problem.id} — {gm.problem.name}' закрыт.")
            self._context = None
        self._wait_for_enter()

    def _action_calculate_ahp(self) -> None:
        if not self._ensure_context_loaded():
            self._wait_for_enter()
            return

        context = self._context
        assert context is not None

        print("\n=== AHP: валидация модели ===")
        validator = Validator(context)
        percent_ok = validator.validate(strict=True)
        print(f"Процент корректности (strict): {percent_ok}%")

        errors = validator.get_errors()
        if errors:
            print("Обнаружены проблемы:")
            for err in errors:
                print(f"  - {err}")
        else:
            print("Ошибок валидации не обнаружено.")

        print("\n=== AHP: расчёт ===")
        ahp = AHP(context)
        try:
            result = ahp.solve()
        except Exception as e:
            print(f"Ошибка при расчёте AHP: {e}")
            self._wait_for_enter()
            return

        gm = context.group_model

        print("\nВеса критериев:")
        for crit in gm.model.criteria:
            w = result.criteria_weights.get(crit.id, 0.0)
            print(f"  {crit.id:18s} ({crit.name}): {w:.4f}")

        print(
            f"\nСогласованность матрицы критериев:"
            f" OS={result.criteria_consistency_os:.4f}, "
            f"{result.criteria_consistency_percent:.2f}%"
        )

        print("\nГлобальные веса альтернатив:")
        alt_sorted = sorted(
            gm.model.alternatives,
            key=lambda a: result.global_alt_weights.get(a.id, 0.0),
            reverse=True,
        )
        for alt in alt_sorted:
            w = result.global_alt_weights.get(alt.id, 0.0)
            print(f"  {alt.id:15s} ({alt.name}): {w:.4f}")

        if gm.pairwise_matrices.criteria_level:
            print("\n" + "-" * 60)
            print("МАТРИЦЫ ПОПАРНЫХ СРАВНЕНИЙ (AHP)")
            print("-" * 60)

            print("\n[КРИТЕРИИ — матрицы по экспертам]")
            for idx, m in enumerate(gm.pairwise_matrices.criteria_level, start=1):
                title = f"Эксперт {m.expert_id} (матрица #{idx})"
                self._matrix_printer.print_matrix(
                    matrix=m.matrix,
                    row_labels=m.items,
                    col_labels=m.items,
                    title=title,
                )
                print()

            print("\n[АЛЬТЕРНАТИВЫ — по критериям и экспертам]")
            for idx, m in enumerate(gm.pairwise_matrices.alternative_level, start=1):
                title = (
                    f"Критерий {m.criterion_id}, эксперт {m.expert_id} "
                    f"(матрица #{idx})"
                )
                self._matrix_printer.print_matrix(
                    matrix=m.matrix,
                    row_labels=m.items,

                    col_labels=m.items,
                    title=title,
                )
                print()

        self._wait_for_enter()

    def _action_calculate_aemcom(self) -> None:
        if not self._ensure_context_loaded():
            self._wait_for_enter()
            return

        context = self._context
        assert context is not None

        print("\n=== AEM-COM: запуск ===")
        aem = AemCom(context)

        try:
            global_result = aem.run_full()
        except Exception as e:
            print(f"Ошибка при расчёте AEM-COM: {e}")
            self._wait_for_enter()
            return

        print(
            f"\nВсего уровней обработано: {global_result.levels_count}, "
            f"суммарное число итераций: {global_result.total_iterations}"
        )

        gm = context.group_model

        if global_result.criteria_result is not None:
            print("\n" + "-" * 60)
            print("[AEM-COM] УРОВЕНЬ КРИТЕРИЕВ")
            print("-" * 60)

            crit_run = global_result.criteria_result.run

            print(
                f"GCOMPI: initial={crit_run.gcompi_initial:.6f}, "
                f"final={crit_run.gcompi_final:.6f}, "
                f"min(A, w_G)={crit_run.gcompi_min:.6f}"
            )
            print(f"Итераций: {crit_run.iterations}")

            print("\nВекторы приоритетов (критерии):")
            for item, v0, v_fin, w in zip(
                crit_run.items,
                crit_run.initial_priorities,
                crit_run.final_priorities,
                crit_run.group_priorities,
            ):
                print(
                    f"  {item}: v0={v0:.4f}, v'={v_fin:.4f}, w_G={w:.4f}"
                )

            self._matrix_printer.print_matrix(
                matrix=crit_run.initial_matrix,
                row_labels=crit_run.items,
                col_labels=crit_run.items,
                title="\nP0 (коллективная матрица критериев, до AEM-COM)",
            )
            print()
            self._matrix_printer.print_matrix(
                matrix=crit_run.final_matrix,
                row_labels=crit_run.items,
                col_labels=crit_run.items,
                title="\nP' (коллективная матрица критериев, после AEM-COM)",
            )

            if crit_run.history:
                print("\nПервые несколько итераций (критерии):")
                for rec in crit_run.history[:5]:
                    print(
                        f"  it={rec.iteration:2d}, pair={rec.pair_items}, "
                        f"t={rec.t_rs:.4f}, old={rec.old_value:.4f}, "
                        f"new={rec.new_value:.4f}, GCOMPI={rec.gcompi_value:.6f}"
                    )

        print("\n" + "-" * 60)
        print("[AEM-COM] УРОВЕНЬ АЛЬТЕРНАТИВ ПО КРИТЕРИЯМ")
        print("-" * 60)

        for crit in gm.model.criteria:
            c_id = crit.id
            if c_id not in global_result.alternatives_results:
                continue

            alt_res = global_result.alternatives_results[c_id]
            run = alt_res.run

            print(f"\nКритерий {c_id} ({crit.name}):")
            print(
                f"  GCOMPI: initial={run.gcompi_initial:.6f}, "
                f"final={run.gcompi_final:.6f}, "
                f"min(A, w_G)={run.gcompi_min:.6f}"
            )
            print(f"  Итераций: {run.iterations}")

            print("  Векторы приоритетов (альтернативы):")
            for item, v0, v_fin, w in zip(
                run.items,
                run.initial_priorities,
                run.final_priorities,
                run.group_priorities,
            ):
                print(
                    f"    {item}: v0={v0:.4f}, v'={v_fin:.4f}, w_G={w:.4f}"
                )

            self._matrix_printer.print_matrix(
                matrix=run.initial_matrix,
                row_labels=run.items,
                col_labels=run.items,
                title=f"\nP0 (альтернативы, критерий {c_id})",
            )
            print()
            self._matrix_printer.print_matrix(
                matrix=run.final_matrix,
                row_labels=run.items,
                col_labels=run.items,
                title=f"\nP' (альтернативы, критерий {c_id})",
            )

            if run.history:
                last = run.history[-1]
                print(
                    f"\n  Последняя итерация:"
                    f" it={last.iteration}, pair={last.pair_items},"
                    f" t={last.t_rs:.4f}, GCOMPI={last.gcompi_value:.6f}"
                )

        if context.result_save_path:
            try:
                saved_to = context.save_result_json()
                print(f"\nРезультат сохранён в: {saved_to}")
            except Exception as e:
                print(f"\nОшибка авто-сохранения результата: {e}")

        self._wait_for_enter()

    def _ensure_context_loaded(self) -> bool:
        if self._context is None:
            print("Контекст не загружен. Сначала выберите JSON-файл (пункт 1).")
            return False
        return True