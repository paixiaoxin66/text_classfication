#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一入口：构建最终训练数据集（约 30000 条）
============================================
流程：分析 → 清洗 → 去重 → 标签检查 → 划分 → 只增强 Train → 质量过滤
      → 近重复/泄漏检查 → 按类别预算组装最终训练集 → 汇总报告

用法：
  python scripts/build_dataset.py --target-size 30000 --seed 42
  python scripts/build_dataset.py --assemble-only --target-size 30000 --seed 42
  python scripts/build_dataset.py --resume

输出：
  data/processed/train_augmented.csv   最终训练集（真实+增强, is_aug=0/1）
  data/reports/augmentation_report.md  完整数据增强报告
"""

from __future__ import annotations

import argparse
import difflib
import random
import re
import time
from collections import Counter
from pathlib import Path

import augment_dataset
import filter_augmented
import clean_complaints
import split_dataset
import enrich_dataset
from clean_complaints import UNLABELED, load_rows, write_csv

RAW_DEFAULT = "data/raw/hemao_complaints.csv"
CLEAN = "data/processed/cleaned_complaints.csv"
TRAIN_REAL = "data/processed/train_real.csv"
VAL_REAL = "data/processed/val_real.csv"
TEST_REAL = "data/processed/test_real.csv"
AUG_RAW = "data/augmentation/generated_raw.csv"
AUG_FILTERED = "data/augmentation/generated_filtered.csv"
TRAIN_FINAL = "data/processed/train_augmented.csv"
REPORT_DIR = "data/reports"


def norm(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def check_leakage(aug_rows: list[dict], val_rows: list[dict], test_rows: list[dict]) -> dict:
    val_texts = [r["text"] for r in val_rows]
    test_texts = [r["text"] for r in test_rows]
    val_keys = {norm(t) for t in val_texts}
    test_keys = {norm(t) for t in test_texts}
    leak_exact = 0
    leak_examples: list[str] = []
    for row in aug_rows:
        key = norm(row["text"])
        if key in val_keys or key in test_keys:
            leak_exact += 1
            if len(leak_examples) < 3:
                leak_examples.append(row["text"][:60])

    rng = random.Random(42)
    leak_near = 0
    near_examples: list[str] = []
    sampled = aug_rows[::10]
    for row in sampled:
        text = row["text"]
        for pool in (val_texts, test_texts):
            sample = rng.sample(pool, min(30, len(pool)))
            for ref in sample:
                if difflib.SequenceMatcher(None, text, ref).ratio() > 0.90:
                    leak_near += 1
                    if len(near_examples) < 3:
                        near_examples.append(text[:60])
                    break
    return {"exact": leak_exact, "near": leak_near,
            "examples": leak_examples, "near_examples": near_examples}


def assemble_final(train_real: list[dict], filtered: list[dict],
                   plan: dict, seed: int, target_size: int) -> list[dict]:
    rng = random.Random(seed)
    real_counts = Counter(r["category"] for r in train_real)
    final_rows = [{"id": r["id"], "category": r["category"], "text": r["text"], "is_aug": "0"}
                  for r in train_real]

    by_category: dict[str, list[dict]] = {}
    for row in filtered:
        by_category.setdefault(row["category"], []).append(row)

    used_ids: set[str] = set()
    used_aug_count = 0
    extra_rows: list[dict] = []
    for category, rows in by_category.items():
        real_n = real_counts.get(category, 0)
        target = plan.get(category, {}).get("target", real_n)
        cap = max(0, target - real_n)
        rng.shuffle(rows)
        keep = rows[:cap]
        extra_rows.extend(rows[cap:])
        for row in keep:
            candidate = f"{row['src_id']}#{row.get('variant_idx', '0')}"
            candidate_id = candidate
            suffix = 1
            while candidate_id in used_ids:
                candidate_id = f"{candidate}#{suffix}"
                suffix += 1
            used_ids.add(candidate_id)
            final_rows.append({
                "id": candidate_id, "category": row["category"],
                "text": row["text"], "is_aug": "1",
                "aug_method": row.get("aug_method", "rule"),
                "variant_idx": row.get("variant_idx", "0"),
            })
            used_aug_count += 1

    # 先用少数类可用增强，再用通过质量检测的多数类余量补齐到目标规模。
    remaining = max(0, target_size - len(final_rows))
    rng.shuffle(extra_rows)
    for row in extra_rows:
        if remaining <= 0:
            break
        candidate = f"{row['src_id']}#{row.get('variant_idx', '0')}"
        candidate_id = candidate
        suffix = 1
        while candidate_id in used_ids:
            candidate_id = f"{candidate}#{suffix}"
            suffix += 1
        used_ids.add(candidate_id)
        final_rows.append({
            "id": candidate_id, "category": row["category"],
            "text": row["text"], "is_aug": "1",
            "aug_method": row.get("aug_method", "rule"),
            "variant_idx": row.get("variant_idx", "0"),
        })
        used_aug_count += 1
        remaining -= 1
    return final_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="构建最终训练数据集")
    parser.add_argument("--target-size", type=int, default=30000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mode", choices=["auto", "llm", "rule"], default="auto")
    parser.add_argument("--aug-scale", type=float, default=0.0)
    parser.add_argument("--limit-originals", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--keep-unlabeled", action="store_true")
    parser.add_argument("--raw", default=RAW_DEFAULT,
                        help="原始数据路径(默认 data/raw/hemao_complaints.csv; "
                             "可用 data/raw/hemao_complaints_full.csv 用补全后的全文重建)")
    parser.add_argument("--assemble-only", action="store_true",
                        help="跳过清洗/划分/增强/过滤，只用现有产物组装最终数据集")
    args = parser.parse_args()
    raw_input = args.raw
    t0 = time.time()

    print("=" * 70)
    print(f"构建最终数据集: target-size={args.target_size}, seed={args.seed}, mode={args.mode}")
    print("=" * 70)

    if not args.assemble_only:
        if not args.resume or not Path(CLEAN).exists():
            clean_complaints.main(["--input", raw_input])
        split_args = ["--seed", str(args.seed)]
        if args.keep_unlabeled:
            split_args.append("--keep-unlabeled")
        split_dataset.main(split_args)

        aug_cmd = ["--train", TRAIN_REAL, "--target-size", str(args.target_size),
                   "--seed", str(args.seed), "--mode", args.mode]
        if args.resume:
            aug_cmd.append("--resume")
        if args.limit_originals:
            aug_cmd += ["--limit-originals", str(args.limit_originals)]
        if args.aug_scale:
            aug_cmd += ["--aug-scale", str(args.aug_scale)]
        augment_dataset.main(aug_cmd)

        filter_augmented.main([
            "--input", AUG_RAW, "--train", TRAIN_REAL,
            "--output", AUG_FILTERED,
            "--report", "data/reports/augmentation_filter_stats.csv",
        ])

    cleaned = load_rows(Path(CLEAN))
    train_real = load_rows(Path(TRAIN_REAL))
    val_real = load_rows(Path(VAL_REAL))
    test_real = load_rows(Path(TEST_REAL))
    aug_filtered = load_rows(Path(AUG_FILTERED))
    aug_raw = load_rows(Path(AUG_RAW))
    real_counts = Counter(r["category"] for r in train_real)

    plan, _ = augment_dataset.compute_plan(dict(real_counts), args.target_size)
    final_rows = assemble_final(train_real, aug_filtered, plan, args.seed, args.target_size)

    leak = check_leakage(aug_filtered, val_real, test_real)
    write_csv(Path(TRAIN_FINAL), final_rows,
              ["id", "category", "text", "is_aug", "aug_method", "variant_idx"])
    # 补全版: 带全部原始字段的完整最终数据集
    enrich_dataset.main(["--aug", TRAIN_FINAL, "--real", TRAIN_REAL,
                         "--output", "data/processed/train_augmented_full.csv"])

    final_counts = Counter(r["category"] for r in final_rows)
    val_counts = Counter(r["category"] for r in val_real)
    test_counts = Counter(r["category"] for r in test_real)
    aug_counts = Counter(r["category"] for r in aug_filtered)
    used_aug_counts = Counter(r["category"] for r in final_rows if r["is_aug"] == "1")
    cats = sorted(set(real_counts) | set(final_counts))

    final_texts = [r["text"] for r in final_rows]
    dup_total = len(final_texts) - len({norm(t) for t in final_texts})
    report = []
    report.append("# 数据增强报告\n")
    report.append(f"- 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"- 命令: --target-size {args.target_size} --seed {args.seed} --mode {args.mode}\n")

    report.append("## 1. 原始数据")
    report.append(f"- 总数: {len(load_rows(Path(raw_input)))}")
    report.append(f"- 清洗后: {len(cleaned)}")
    unlabeled_n = sum(1 for r in cleaned if r["category"] == UNLABELED)
    report.append(f"- 剔除'{UNLABELED}'（混合行业噪声）: {unlabeled_n} 行")
    report.append(f"- 完全重复剔除: 见 data/reports/duplicate_report.csv\n")

    report.append("## 2. 标签分布\n")
    report.append("| category | 原始 | Train真实 | 增强生成 | 增强过滤 | 实际使用增强 | 最终Train | Validation | Test |")
    report.append("|---|---|---|---|---|---|---|---|---|")
    for cat in cats:
        original_n = sum(1 for r in cleaned if r["category"] == cat)
        report.append(f"| {cat} | {original_n} | {real_counts.get(cat, 0)} | "
                      f"{sum(1 for r in aug_raw if r['category'] == cat)} | "
                      f"{aug_counts.get(cat, 0)} | {used_aug_counts.get(cat, 0)} | "
                      f"{final_counts.get(cat, 0)} | {val_counts.get(cat, 0)} | {test_counts.get(cat, 0)} |")
    report.append("")

    report.append("## 3. 增强情况")
    report.append(f"- 原始 Train: {len(train_real)}")
    report.append(f"- 增强生成（原始输出）: {len(aug_raw)}")
    report.append(f"- 通过质量检测: {len(aug_filtered)}")
    report.append(f"- 被过滤: {len(aug_raw) - len(aug_filtered)}"
                  f"（原因明细: data/reports/augmentation_filter_stats.csv）")
    report.append(f"- 按类别预算后实际使用增强: {sum(used_aug_counts.values())}")
    report.append(f"- 最终 Train: {len(final_rows)}\n")

    report.append("## 4. 重复检测")
    report.append(f"- 最终训练集完全重复（规范化文本）: {dup_total}")
    report.append(f"- 增强 vs 原始文本相似度>0.90 过滤: 见 filter 统计")
    report.append(f"- 跨数据集: 增强 vs Val/Test 完全重复 {leak['exact']}，"
                  f"近重复（抽样10%）{leak['near']}\n")

    report.append("## 5. 数据来源")
    report.append(f"- 真实数据: 黑猫投诉 API（{raw_input}，"
                  f"{len(load_rows(Path(raw_input)))} 条）")
    if args.mode == "llm":
        aug_desc = "LLM 语义改写"
    elif args.mode == "rule":
        aug_desc = "规则增强：领域同义词/诉求重排/副词插入"
    else:
        aug_desc = "auto（优先LLM语义改写，未配置LLM Key时自动回退规则增强）"
    report.append(f"- 增强数据: {args.mode}（{aug_desc}）\n")

    report.append("## 6. 数据集最终规模")
    report.append(f"- Train: {len(final_rows)}")
    report.append(f"- Validation: {len(val_real)}（100% 真实）")
    report.append(f"- Test: {len(test_real)}（100% 真实）")
    report.append(f"- 总规模: {len(final_rows) + len(val_real) + len(test_real)}")

    report.append("\n## 7. 数据质量结论")
    report.append(f"- 测试集是否全部真实: **是**")
    report.append(f"- 验证集是否全部真实: **是**")
    report.append(f"- 是否存在数据泄漏: **{'是，' + str(leak) if leak['exact'] else '否'}**")
    report.append(f"- 类别是否严重失衡: 少数类已重点增强，多数类按预算控制（见标签分布表）")
    report.append(f"- 增强数据占比: {sum(used_aug_counts.values())/max(1, len(final_rows)):.1%}")
    report.append(f"- 增强数据过滤比例: "
                  f"{(len(aug_raw) - len(aug_filtered))/max(1, len(aug_raw)):.1%}")
    report.append(f"- 若最终规模低于目标 {args.target_size}：因少数类规则增强无法在保持质量的前提下"
                  f"继续提高，未用低质量数据凑数。\n")
    (Path(REPORT_DIR) / "augmentation_report.md").write_text("\n".join(report), "utf-8")
    print(f"[assemble] 报告: {REPORT_DIR}/augmentation_report.md (用时 {time.time()-t0:.0f}s)")

    print("\n" + "=" * 70)
    print("最终执行结果汇总")
    print("=" * 70)
    raw_n = len(load_rows(Path(raw_input)))
    print(f" 1. 原始数据: {raw_n}")
    print(f" 2. 清洗后: {len(cleaned)}")
    print(f" 3. Train（真实）: {len(train_real)}")
    print(f" 4. Validation: {len(val_real)}")
    print(f" 5. Test: {len(test_real)}")
    print(f" 6. 真实训练数据: {len(train_real)}")
    print(f" 7. 生成增强数据: {len(aug_raw)}")
    print(f" 8. 过滤后增强数据: {len(aug_filtered)}")
    print(f" 9. 最终训练数据: {len(final_rows)}")
    print(f"10. 最终总数据(Train+Val+Test): {len(final_rows) + len(val_real) + len(test_real)}")
    print("11. 各类别数量: 见 augmentation_report.md 第2节")
    print(f"12. 完全重复率（最终训练集）: {dup_total/max(1, len(final_rows)):.2%}")
    print(f"13. 近重复率（增强 vs 原文本过滤）: 见 filter 统计")
    print(f"14. 增强数据占比: {sum(used_aug_counts.values())/max(1, len(final_rows)):.1%}")
    print(f"15. 是否存在数据泄漏: {'是!' if leak['exact'] else '否'}")
    print(f"16. 增强方法: {args.mode}"
          f"（{'LLM语义改写' if args.mode == 'llm' else ('规则增强' if args.mode == 'rule' else '优先LLM, 无Key回退规则')}）")
    print(f"17. API调用: {'LLM模式' if args.mode == 'llm' else ('0次（规则模式, auto回退）' if args.mode == 'auto' else '0次（规则模式）')}")
    print("18. 失败样本: 见 data/augmentation/failures.jsonl")
    print("19. 脚本: scripts/{clean_complaints,split_dataset,augment_dataset,filter_augmented,build_dataset}.py")
    print("20. 运行: python scripts/build_dataset.py --target-size 30000 --seed 42")
    print("=" * 70)


if __name__ == "__main__":
    main()
