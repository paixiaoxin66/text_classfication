#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把抓到的详情页全文回填到原始数据(生成 patched 副本, 不修改原文件)
============================================================
流程: fetch_full_text.py 产出 data/raw/full_text_patch.csv 后运行本脚本:
  1) 复制 data/raw/hemao_complaints.csv → data/raw/hemao_complaints_full.csv
  2) 对 patch 中 ok=1 的行, 用 full_text 替换 summary 字段
  3) 校验后输出, 供 build_dataset.py --raw 使用

用法:
  python scripts/apply_full_text.py
  python scripts/build_dataset.py --target-size 30000 --seed 42 --raw data/raw/hemao_complaints_full.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="回填详情页全文, 生成 patched 原始数据")
    p.add_argument("--input", default="data/raw/hemao_complaints.csv")
    p.add_argument("--patch", default="data/raw/full_text_patch.csv")
    p.add_argument("--output", default="data/raw/hemao_complaints_full.csv")
    args = p.parse_args()

    rows = list(csv.DictReader(open(args.input, encoding="utf-8-sig")))
    patch = {r["id"]: r["full_text"]
             for r in csv.DictReader(open(args.patch, encoding="utf-8-sig"))
             if r["ok"] == "1" and r["full_text"].strip()}
    print(f"原始 {len(rows)} 行, 可用补丁 {len(patch)} 条")

    replaced, skipped = 0, 0
    for r in rows:
        full = patch.get(r["id"], "")
        if not full:
            continue
        if len(full) <= len(r.get("summary", "")):
            skipped += 1  # 抓到的比原 summary 还短, 视为无效, 不替换
            continue
        r["summary"] = full
        replaced += 1

    fieldnames = list(rows[0].keys())
    out = Path(args.output)
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"完成: 替换 {replaced} 行, 跳过(比原summary短) {skipped} 行")
    print(f"输出: {out}  (原文件未动)")


if __name__ == "__main__":
    main()
