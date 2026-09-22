#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基线消融实验: 纯真实 vs 纯增强 vs 混合 —— 分开验证
============================================================
三种训练集互不掺和, 全部用同一套真实 Val/Test 评估:
  R  纯真实   : data/processed/train_real.csv            (6893)
  A  纯增强   : data/processed/train_augmented.csv 中 is_aug=1 (23107)
  M  混合     : data/processed/train_augmented.csv            (30000)

每个配置: TF-IDF + NB/LR, 验证集选优, 测试集报告 macro-F1/weighted-F1/准确率。
输出: data/out_ablation/ablation_results.csv + ablation_report.md

用法:
  uv run python scripts/train_baseline_ablation.py                  # 默认分词
  uv run python scripts/train_baseline_ablation.py --tokenizer char_wb  # 字符级n-gram
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report, f1_score)
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC

SEED = 42
TRAIN_REAL = "data/processed/train_real.csv"
VAL_REAL = "data/processed/val_real.csv"
TEST_REAL = "data/processed/test_real.csv"
TRAIN_AUG = "data/processed/train_augmented.csv"
# 按分词方案分开存输出, 避免覆盖
def out_dir(tokenizer: str) -> Path:
    return Path("data/out_ablation") / tokenizer


def load_split(path: Path, aug_only: bool = False) -> tuple[list[str], list[str]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if aug_only:
        rows = [r for r in rows if r["is_aug"] == "1"]
    return [r["text"] for r in rows], [r["category"] for r in rows]


def make_vectorizer(tokenizer: str):
    if tokenizer == "char_wb":
        return TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4),
                               max_features=50000, sublinear_tf=True, min_df=2)
    return TfidfVectorizer(max_features=50000, ngram_range=(1, 2),
                           sublinear_tf=True, min_df=2)


def run_config(name: str, train_path: str, aug_only: bool,
               X_val, y_val, X_test, y_test, tokenizer: str) -> dict:
    print(f"\n{'='*60}\n配置 [{name}] 训练集加载...")
    X_tr, y_tr = load_split(Path(train_path), aug_only)
    labels = sorted(set(y_tr))
    print(f"  训练 {len(X_tr)} / 验证 {len(X_val)} / 测试 {len(X_test)} / 类别 {len(labels)}")

    vec = make_vectorizer(tokenizer)
    X_tr_v = vec.fit_transform(X_tr)
    X_val_v = vec.transform(X_val)
    X_test_v = vec.transform(X_test)

    candidates = {
        "朴素贝叶斯(MultinomialNB)": MultinomialNB(alpha=1.0),
        "逻辑回归(LogisticRegression)": LogisticRegression(max_iter=1000, C=1.0, random_state=SEED),
        "线性SVM(LinearSVC)": LinearSVC(max_iter=5000, C=1.0, random_state=SEED),
    }
    best_name, best_model, best_f1 = None, None, -1.0
    for name_m, model in candidates.items():
        model.fit(X_tr_v, y_tr)
        vf = f1_score(y_val, model.predict(X_val_v), average="macro")
        print(f"    {name_m}: 验证 macro-F1 = {vf:.4f}")
        if vf > best_f1:
            best_name, best_model, best_f1 = name_m, model, vf
    print(f"  选用: {best_name} (验证 macro-F1={best_f1:.4f})")

    y_pred = best_model.predict(X_test_v)
    acc = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average="macro")
    f1_weighted = f1_score(y_test, y_pred, average="weighted")
    print(f"  测试集: 准确率={acc:.4f}  macro-F1={f1_macro:.4f}  weighted-F1={f1_weighted:.4f}")

    # 保存单个配置的完整报告 + 模型
    cfg_dir = out_dir(tokenizer) / name
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "baseline_report.txt").write_text(
        f"=== [{name}] {best_name} ===\n"
        f"训练{len(X_tr)} 验证{len(X_val)} 测试{len(X_test)} 类别{len(labels)}\n"
        f"准确率={acc:.4f}  macro-F1={f1_macro:.4f}  weighted-F1={f1_weighted:.4f}\n\n"
        + classification_report(y_test, y_pred, digits=4), "utf-8")
    joblib.dump({"vectorizer": vec, "model": best_model, "labels": labels,
                 "config": name, "train_size": len(X_tr)}, cfg_dir / "model.joblib")
    (cfg_dir / "label_map.json").write_text(
        json.dumps({l: i for i, l in enumerate(labels)}, ensure_ascii=False, indent=2), "utf-8")

    return {"config": name, "train_size": len(X_tr), "best_model": best_name,
            "val_macro_f1": round(best_f1, 4), "test_acc": round(acc, 4),
            "test_macro_f1": round(f1_macro, 4), "test_weighted_f1": round(f1_weighted, 4)}


def main() -> None:
    p = argparse.ArgumentParser(description="基线消融: 纯真实 vs 纯增强 vs 混合")
    p.add_argument("--tokenizer", choices=["default", "char_wb"], default="default")
    args = p.parse_args()

    X_val, y_val = load_split(Path(VAL_REAL))
    X_test, y_test = load_split(Path(TEST_REAL))
    print(f"Val {len(X_val)} / Test {len(X_test)} (100% 真实, 三配置共用)")

    configs = [
        ("R_纯真实", TRAIN_REAL, False),
        ("A_纯增强", TRAIN_AUG, True),
        ("M_真实加增强", TRAIN_AUG, False),
    ]
    results = []
    for name, path, aug_only in configs:
        results.append(run_config(name, path, aug_only, X_val, y_val, X_test, y_test,
                                  args.tokenizer))

    # 汇总
    od = out_dir(args.tokenizer)
    od.mkdir(parents=True, exist_ok=True)
    cols = ["config", "train_size", "best_model", "val_macro_f1", "test_acc",
            "test_macro_f1", "test_weighted_f1"]
    with open(od / "ablation_results.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(results)

    md = ["# 基线消融实验报告（分开验证）\n",
          f"- 分词: {args.tokenizer}  |  Val/Test 100% 真实(共用)  |  seed {SEED}\n",
          "| 配置 | 训练集大小 | 选用模型 | Val macro-F1 | Test准确率 | Test macro-F1 | Test weighted-F1 |",
          "|---|---|---|---|---|---|---|"]
    for r in results:
        md.append(f"| {r['config']} | {r['train_size']} | {r['best_model'].split('(')[0]} | "
                  f"{r['val_macro_f1']} | {r['test_acc']} | {r['test_macro_f1']} | {r['test_weighted_f1']} |")
    md += ["",
           "## 结论要点",
           "- 纯增强(A) vs 纯真实(R): 判断合成数据单独能否支撑分类",
           "- 混合(M) vs 纯真实(R): 判断增强是否带来净提升(答辩核心)",
           "- Val/Test 恒为真实数据, 三配置完全隔离, 无泄漏",
           "",
           "模型/逐类报告见本目录子目录。"]
    (od / "ablation_report.md").write_text("\n".join(md), "utf-8")

    print(f"\n{'='*60}\n汇总:")
    for r in results:
        print(f"  {r['config']:<10} train={r['train_size']:>6} | "
              f"valF1={r['val_macro_f1']:.4f} | testAcc={r['test_acc']:.4f} | "
              f"testMacroF1={r['test_macro_f1']:.4f} | testWtF1={r['test_weighted_f1']:.4f}")
    print(f"\n已保存: {od/'ablation_results.csv'} 和 {od/'ablation_report.md'}")


if __name__ == "__main__":
    main()
