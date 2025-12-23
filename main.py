from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional, Sequence

from console.interaction import MainMenu
from modules import Context, AemCom


def _expand_short_bundles(argv: Sequence[str]) -> List[str]:
    bool_flags = {"a"}
    arg_flags = {"f", "o"}

    out: List[str] = []
    argv_list = list(argv)
    i = 0

    while i < len(argv_list):
        tok = argv_list[i]
        if tok.startswith("--") or not tok.startswith("-") or tok == "-" or len(tok) == 2:
            out.append(tok)
            i += 1
            continue

        bundle = tok[1:]
        j = 0
        while j < len(bundle):
            ch = bundle[j]
            if ch in bool_flags:
                out.append("-" + ch)
                j += 1
                continue
            if ch in arg_flags:
                out.append("-" + ch)
                rest = bundle[j + 1 :]
                if rest:
                    out.append(rest)
                j = len(bundle)
                break

            out.append(tok)
            j = len(bundle)
            break

        i += 1

    return out


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="aemcom",
        description="AHP / AEM-COM console tool",
        add_help=True,
    )

    parser.add_argument(
        "-f",
        "--file",
        dest="file",
        metavar="PATH",
        help="Путь к JSON-файлу задачи (контекст)",
    )
    parser.add_argument(
        "-a",
        "--auto",
        dest="auto",
        action="store_true",
        help="Автоматически выполнить AEM-COM и завершиться (нужен -f)",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        metavar="DIR",
        help="Папка (или путь .json) для сохранения результата. Если указано в --auto, stdout будет пустой.",
    )

    return parser.parse_args(list(argv))


def _json_default(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, tuple):
        return list(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _run_auto(args) -> int:
    if not args.file:
        print("Ошибка: для --auto / -a нужно указать --file / -f <путь к json>", file=sys.stderr)
        return 2

    context = Context.from_json_file(args.file, result_save_path=args.output)

    AemCom(context).run_full()

    if context.result_save_path:
        context.save_result_json()
        return 0

    payload = context.build_result_payload()
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    argv = _expand_short_bundles(argv)
    args = _parse_args(argv)

    if args.auto:
        return _run_auto(args)

    menu = MainMenu()

    if args.file:
        menu.load_context_from_file(args.file, output_path=args.output, wait_after=False)

    menu.run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
