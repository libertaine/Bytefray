"""Run current-product pytest; optionally omit the exact reviewed research inventory."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "tools/ci_reduced_inventory.json"


def reduced_modules() -> list[str]:
    modules = json.loads(INVENTORY.read_text(encoding="utf-8"))["modules"]
    if len(modules) != len(set(modules)) or any(not (ROOT / p).is_file() for p in modules):
        raise ValueError("invalid reduced-suite inventory")
    return modules


def main() -> int:
    args = sys.argv[1:]
    reduced = "--reduced" in args
    if reduced:
        args.remove("--reduced")
    ignores = [f"--ignore={path}" for path in reduced_modules()] if reduced else []
    print(f"product suite: {'reduced' if reduced else 'full'}; "
          f"{len(ignores)} inventoried research modules omitted", flush=True)
    return subprocess.call([sys.executable, "-m", "pytest", *ignores, *args], cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
