#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强数据质量过滤 + 近重复检测
==============================
对 augment_dataset.py 生成的原始增强文本做质量把关：
  * 空/过短
  * 与原文本完全相同或字符相似度过高
  * 与已通过增强样本过度相似（模板泛滥）
  * 含 LLM 元话术
  * 金额被篡改
  * 品牌（投诉对象）丢失
  * 标签异常

输出保留 src_id / variant_idx / aug_method，便于最终数据集生成可追溯 ID。

用法：
  python scripts/filter_augmented.py
"""

from __future__ import annotations

import argparse
import csv
import difflib
import re
from collections import Counter
from pathlib import Path

LLM_META = ["作为AI", "作为人工智能", "根据您的要求", "以下是", "希望我的回答",
            "作为一名", "很高兴为您", "谢谢您的", "抱歉，我无法", "很抱歉，"]
RE_AMOUNT = re.compile(r"\d+(?:\.\d+)?\s*(?:元|块|块钱|rmb|¥|￥)")


def nz(value) -> str:
    return (value or "").strip()


def load_rows(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in columns})


def norm(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def trigrams(text: str) -> set[str]:
    if len(text) < 3:
        return {text}
    return {text[i:i + 3] for i in range(len(text) - 2)}


def jaccard(a: set[str], b: set[str]) -> float:
    union = len(a) | len(b)
    if union == 0:
        return 0.0
    return len(a & b) / union


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="增强数据质量过滤")
    parser.add_argument("--input", default="data/augmentation/generated_raw.csv")
    parser.add_argument("--train", default="data/processed/train_real.csv")
    parser.add_argument("--output", default="data/augmentation/generated_filtered.csv")
    parser.add_argument("--report", default="data/reports/augmentation_filter_stats.csv")
    parser.add_argument("--sim-threshold", type=float, default=0.90)
    parser.add_argument("--sim-sample", type=float, default=0.88)
    parser.add_argument("--min-len", type=int, default=15)
    args = parser.parse_args(argv)

    generated = load_rows(Path(args.input))
    originals = {r["id"]: r for r in load_rows(Path(args.train))}
    print(f"待过滤增强样本: {len(generated)}")

    reasons: Counter = Counter()
    passed: list[dict] = []
    accepted_by_category: dict[str, list[tuple[str, set[str]]]] = {}
    seen_norm: set[str] = set()
    for g in generated:
        text = nz(g.get("text"))
        src_id = nz(g.get("src_id"))
        category = nz(g.get("category"))
        variant_idx = nz(g.get("variant_idx")) or "0"
        aug_method = nz(g.get("aug_method")) or "rule"

        if len(text) < args.min_len:
            reasons["过短(<%d字)" % args.min_len] += 1
            continue

        key = norm(text)
        if key in seen_norm:
            reasons["与已有增强文本完全相同"] += 1
            continue

        original = originals.get(src_id)
        if original is not None:
            orig_text = original.get("text", "")
            orig_sim = similarity(text, orig_text)
            if orig_sim >= 1.0:
                reasons["与原文本完全相同"] += 1
                continue
            if orig_sim > args.sim_threshold:
                reasons["与原文本相似度过高(>%.2f)" % args.sim_threshold] += 1
                continue
        else:
            reasons["找不到原始母本"] += 1
            continue

        if accepted_by_category:
            pool = accepted_by_category.get(category, [])[-50:]
            text_trigrams = trigrams(text)
            if any(src != src_id and jaccard(text_trigrams, s) > 0.75 for src, s in pool):
                reasons["与已通过样本过度相似"] += 1
                continue

        if any(word in text for word in LLM_META):
            reasons["含LLM元话术"] += 1
            continue

        amount_orig = set(RE_AMOUNT.findall(original["text"]))
        amount_new = set(RE_AMOUNT.findall(text))
        if amount_orig and amount_orig != amount_new:
            reasons["金额被篡改"] += 1
            continue

        brand = nz(original.get("cotitle"))
        if brand and len(norm(brand)) >= 2:
            if norm(brand) in norm(original["text"]) and norm(brand) not in norm(text):
                reasons["品牌/投诉对象丢失"] += 1
                continue

        if not category or not original or original["category"] != category:
            reasons["标签异常"] += 1
            continue

        passed.append({"src_id": src_id, "category": category, "text": text,
                       "aug_method": aug_method, "variant_idx": variant_idx})
        accepted_by_category.setdefault(category, []).append((src_id, trigrams(text)))
        seen_norm.add(key)

    write_csv(Path(args.output), passed,
              ["src_id", "category", "text", "aug_method", "variant_idx"])
    stats = [{"过滤原因": k, "数量": v} for k, v in reasons.most_common()]
    write_csv(Path(args.report), stats, ["过滤原因", "数量"])

    print(f"通过: {len(passed)} | 过滤: {len(generated) - len(passed)}")
    for reason, count in reasons.most_common():
        print(f"  - {reason}: {count}")
    print(f"输出: {args.output}")


if __name__ == "__main__":
    main()
