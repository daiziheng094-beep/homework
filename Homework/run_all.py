#!/usr/bin/env python3
"""Reproduce every table and figure in the report with one command.

Usage
-----
    python3 run_all.py

Put the input file at ``data/raw/public.csv`` first.  Nothing else needs to be
edited: the script rebuilds the analysis sample, both replication tables, all
robustness checks and every figure, and writes them to ``data/processed`` and
``results``.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from config import RAW_FILE, ensure_dirs  # noqa: E402


def main() -> int:
    if not RAW_FILE.exists():
        print(f"ERROR: input file not found at {RAW_FILE.relative_to(ROOT)}", file=sys.stderr)
        print("Place the store-level survey file there and run this script again.", file=sys.stderr)
        return 1

    ensure_dirs()

    # Imported here so the input check runs before any work starts.
    import figures
    import prepare_data
    import replication
    import robustness

    steps = [
        ("构建分析样本 (data/processed)", prepare_data.main),
        ("复制原论文表3与表4 (results/tables)", replication.main),
        ("稳健性与敏感性检验 (results/tables)", robustness.main),
        ("生成图表 (results/figures)", figures.main),
    ]

    for index, (label, run) in enumerate(steps, start=1):
        print("=" * 72)
        print(f"[{index}/{len(steps)}] {label}")
        print("=" * 72)
        started = time.perf_counter()
        run()
        print(f"--- 完成，用时 {time.perf_counter() - started:.1f} 秒\n")

    print("=" * 72)
    print("全部完成。请查看 results/tables 与 results/figures。")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
