#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基线模型: TF-IDF + 朴素贝叶斯/逻辑回归
================================================
对 18 类消费者投诉文本做分类, 作为与 BERT 对比的"传统机器学习基线"。

用法:
  uv run python train_baseline.py                          # 训练+评估(默认用数据流水线产物)
  uv run python train_baseline.py --demo "京东快递不给我派件"  # 用训练好的模型预测单条文本

默认数据(数据流水线 scripts/build_dataset.py 的产物):
  --train data/processed/train_augmented.csv   # 最终训练集(6886真实 + 23114增强, 30000条)
  --val   data/processed/val_real.csv          # 验证集(854条, 100%真实)
  --test  data/processed/test_real.csv         # 测试集(877条, 100%真实)

输出(到 --out-dir):
  baseline.joblib        训练好的模型+向量器(供 --demo / 部署)
  baseline_report.txt    测试集分类报告(准确率/F1/每类P/R)
  baseline_confusion.png 混淆矩阵图
  label_map.json         类别名<->数字ID 映射

依赖: scikit-learn joblib matplotlib  (已加入 pyproject, uv sync 安装)
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score)
from sklearn.naive_bayes import MultinomialNB

SEED = 42


def load_split(path: Path) -> tuple[list[str], list[str]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return [r["text"] for r in rows], [r["category"] for r in rows]


def plot_confusion(cm: np.ndarray, labels: list[str], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(16, 13))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels)), labels, rotation=90, fontsize=9)
    ax.set_yticks(range(len(labels)), labels, fontsize=9)
    ax.set_xlabel("预测类别")
    ax.set_ylabel("真实类别")
    ax.set_title("混淆矩阵(基线模型, 测试集)")
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            if cm[i, j] > 0:
                ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=7)
    fig.colorbar(im)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description="基线: TF-IDF + 朴素贝叶斯/逻辑回归")
    p.add_argument("--train", default="data/processed/train_augmented.csv")
    p.add_argument("--val", default="data/processed/val_real.csv")
    p.add_argument("--test", default="data/processed/test_real.csv")
    p.add_argument("--out-dir", default="data/out")
    p.add_argument("--demo", default="", help="预测单条文本(需先训练)")
    args = p.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    model_path = out_dir / "baseline.joblib"

    # ---- 演示模式: 用已训练模型预测 ----
    if args.demo:
        bundle = joblib.load(model_path)
        text = args.demo
        proba = bundle["model"].predict_proba(bundle["vectorizer"].transform([text]))[0]
        top = int(np.argmax(proba))
        print(f"文本: {text}")
        print(f"预测类别: {bundle['labels'][top]}  (置信度 {proba[top]:.2%})")
        for i in np.argsort(proba)[::-1][:3]:
            print(f"  {bundle['labels'][i]:　<8} {proba[i]:.1%}")
        return

    # ---- 训练模式 ----
    X_train, y_train = load_split(Path(args.train))
    X_val, y_val = load_split(Path(args.val))
    X_test, y_test = load_split(Path(args.test))
    labels = sorted(set(y_train))
    print(f"训练 {len(X_train)} / 验证 {len(X_val)} / 测试 {len(X_test)} / 类别 {len(labels)}")

    vectorizer = TfidfVectorizer(max_features=50000, ngram_range=(1, 2),
                                 sublinear_tf=True, min_df=2)
    X_train_v = vectorizer.fit_transform(X_train)
    X_val_v = vectorizer.transform(X_val)
    X_test_v = vectorizer.transform(X_test)

    # 训练两种模型, 用验证集选优
    candidates = {
        "朴素贝叶斯(MultinomialNB)": MultinomialNB(alpha=1.0),
        "逻辑回归(LogisticRegression)": LogisticRegression(max_iter=1000, C=1.0, random_state=SEED),
    }
    best_name, best_model, best_f1 = None, None, -1.0
    for name, model in candidates.items():
        model.fit(X_train_v, y_train)
        val_f1 = f1_score(y_val, model.predict(X_val_v), average="macro")
        print(f"{name}: 验证集 macro-F1 = {val_f1:.4f}")
        if val_f1 > best_f1:
            best_name, best_model, best_f1 = name, model, val_f1
    print(f"选用: {best_name} (验证 macro-F1={best_f1:.4f})")

    # 测试集最终评估
    y_pred = best_model.predict(X_test_v)
    acc = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average="macro")
    print(f"测试集: 准确率={acc:.4f}  macro-F1={f1_macro:.4f}")

    report = (
        f"=== 基线模型 {best_name} ===\n"
        f"数据: 训练{len(X_train)} 验证{len(X_val)} 测试{len(X_test)} 类别{len(labels)}\n"
        f"准确率={acc:.4f}  macro-F1={f1_macro:.4f}\n\n"
        + classification_report(y_test, y_pred, digits=4)
    )
    (out_dir / "baseline_report.txt").write_text(report, "utf-8")
    print(report)

    cm = confusion_matrix(y_test, y_pred, labels=labels)
    plot_confusion(cm, labels, out_dir / "baseline_confusion.png")

    # 保存(模型+向量器+标签)供 --demo 和答辩部署
    joblib.dump({"vectorizer": vectorizer, "model": best_model, "labels": labels},
                model_path)
    (out_dir / "label_map.json").write_text(
        json.dumps({lbl: i for i, lbl in enumerate(labels)}, ensure_ascii=False, indent=2), "utf-8")
    print(f"已保存: {model_path}")
    print(f"报告: {out_dir/'baseline_report.txt'}  混淆矩阵: {out_dir/'baseline_confusion.png'}")


if __name__ == "__main__":
    main()
