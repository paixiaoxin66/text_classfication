#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据划分: 真实数据 → Train/Validation/Test (先划分, 后增强)
============================================
硬性要求:
  * 必须从清洗后的真实数据先划分, 再对 Train 做增强
  * Validation / Test 100% 真实, 禁止增强
  * stratified split 保证类别分布一致, 固定 seed=42 可复现
  * 默认剔除"其他/未分类"(混合行业噪声), 可用 --keep-unlabeled 保留

用法:
  python scripts/split_dataset.py

输出:
  data/processed/train_real.csv   (允许增强)
  data/processed/val_real.csv     (禁止增强)
  data/processed/test_real.csv    (禁止增强)
  data/reports/split_distribution.csv  类别 × 各划分数量
"""

from __future__ import annotations

import argparse
import csv
import random
from collections import Counter
from pathlib import Path

from clean_complaints import UNLABELED, load_rows, write_csv

SEED = 42
SPLIT = (0.8, 0.1, 0.1)


def stratified_split(rows: list[dict], seed: int) -> tuple[list, list, list]:
    rng = random.Random(seed)
    by_class: dict[str, list] = {}
    for r in rows:
        by_class.setdefault(r["category"], []).append(r)
    train, val, test = [], [], []
    for cat, group in by_class.items():
        rng.shuffle(group)
        n = len(group)
        n_train = int(n * SPLIT[0])
        n_val = int(n * SPLIT[1])
        train.extend(group[:n_train])
        val.extend(group[n_train:n_train + n_val])
        test.extend(group[n_train + n_val:])
    rng.shuffle(train)
    rng.shuffle(val)
    rng.shuffle(test)
    return train, val, test


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="真实数据分层划分")
    p.add_argument("--input", default="data/processed/cleaned_complaints.csv")
    p.add_argument("--out-dir", default="data/processed")
    p.add_argument("--report-dir", default="data/reports")
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--keep-unlabeled", action="store_true",
                   help="保留'其他/未分类'(默认剔除, 因其为混合行业噪声)")
    args = p.parse_args(argv)
    out_dir = Path(args.out_dir)
    report_dir = Path(args.report_dir)

    rows = load_rows(Path(args.input))
    if not args.keep_unlabeled:
        before = len(rows)
        rows = [r for r in rows if r["category"] != UNLABELED]
        print(f"剔除'{UNLABELED}': {before - len(rows)} 行 (剩余 {len(rows)})")

    train, val, test = stratified_split(rows, args.seed)
    cols = ["id", "category", "text", "title", "summary", "cotitle",
            "appeal", "issue", "status", "datetime", "url"]
    write_csv(out_dir / "train_real.csv", train, cols)
    write_csv(out_dir / "val_real.csv", val, cols)
    write_csv(out_dir / "test_real.csv", test, cols)

    # 划分统计
    dist_rows = []
    cats = sorted({r["category"] for r in rows})
    for c in cats:
        dist_rows.append({
            "category": c,
            "原始": sum(1 for r in rows if r["category"] == c),
            "Train": sum(1 for r in train if r["category"] == c),
            "Validation": sum(1 for r in val if r["category"] == c),
            "Test": sum(1 for r in test if r["category"] == c),
        })
    write_csv(report_dir / "split_distribution.csv", dist_rows,
              ["category", "原始", "Train", "Validation", "Test"])

    print(f"划分完成 (seed={args.seed}): Train {len(train)} / Val {len(val)} / Test {len(test)}")
    print(f"输出: {out_dir/'train_real.csv'}, {out_dir/'val_real.csv'}, {out_dir/'test_real.csv'}")
    print(f"分布表: {report_dir/'split_distribution.csv'}")


if __name__ == "__main__":
    main()
