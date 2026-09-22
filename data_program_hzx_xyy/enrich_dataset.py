#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补全最终数据集: train_augmented.csv → train_augmented_full.csv
============================================================
train_augmented.csv 是训练用精简版(只有 id/category/text/is_aug/aug_method/variant_idx)。
本脚本把每条记录补全为"完整版":
  * 真实行(is_aug=0): 直接合并 train_real.csv 的全部原始字段
  * 增强行(is_aug=1): 按其 src_id 找回源记录, 继承源投诉的 title/summary/cotitle/
    appeal/issue/status/datetime/url, text 用增强后的文本
输出列:
  id, category, text, is_aug, aug_method, variant_idx,
  title, summary, cotitle, appeal, issue, status, datetime, url

用法:
  python scripts/enrich_dataset.py
  或由 build_dataset.py 在组装完成后自动调用。
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

FULL_COLS = ["id", "category", "text", "is_aug", "aug_method", "variant_idx",
             "title", "summary", "cotitle", "appeal", "issue", "status",
             "datetime", "url"]


def load(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FULL_COLS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in FULL_COLS})


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="补全最终数据集(带全字段)")
    p.add_argument("--aug", default="data/processed/train_augmented.csv")
    p.add_argument("--real", default="data/processed/train_real.csv")
    p.add_argument("--output", default="data/processed/train_augmented_full.csv")
    args = p.parse_args(argv)

    aug_rows = load(Path(args.aug))
    real_rows = load(Path(args.real))
    real_by_id = {r["id"]: r for r in real_rows}
    print(f"精简版 {len(aug_rows)} 行, 源记录 {len(real_rows)} 行")

    out: list[dict] = []
    missing = 0
    for r in aug_rows:
        src_id = r["id"].split("#")[0] if r["is_aug"] == "1" else r["id"]
        src = real_by_id.get(src_id)
        if src is None:
            missing += 1
            src = {}
        out.append({
            "id": r["id"], "category": r["category"], "text": r["text"],
            "is_aug": r["is_aug"],
            "aug_method": r.get("aug_method", ""),
            "variant_idx": r.get("variant_idx", ""),
            "title": src.get("title", ""), "summary": src.get("summary", ""),
            "cotitle": src.get("cotitle", ""), "appeal": src.get("appeal", ""),
            "issue": src.get("issue", ""), "status": src.get("status", ""),
            "datetime": src.get("datetime", ""), "url": src.get("url", ""),
        })

    write(Path(args.output), out)
    print(f"完成: {args.output} 共 {len(out)} 行")
    if missing:
        print(f"[警告] {missing} 行找不到源记录(字段留空)")
    else:
        print("所有行均已补全源字段 ✓")

    # 快速校验
    filled = sum(1 for r in out if r["title"] and r["summary"] and r["cotitle"])
    print(f"title+summary+cotitle 全非空: {filled}/{len(out)}")


if __name__ == "__main__":
    main()
