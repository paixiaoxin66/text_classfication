# -*- coding: utf-8 -*-
"""校验 frontend/测试报告.md 的 P1/P2 断言 —— 用真实 BERT 模型(仓库产物)跑
1. 测试报告明确引用的实例文本(网约车/干洗店/4S店 + P2表格典型错误)
2. 真实测试集 test_real.csv 全量 877 条:
   - Top-1 准确率(对照 bert_report.txt 的 85.40%)
   - 平均 Top-1 置信度(报告声称 98.3%)
   - Top1-Top2 差距分布(报告声称 <10% 的为 0 条)
   - 错误样本的平均置信度(报告声称 96.1%)
"""
import os
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import json
import csv
import time
from pathlib import Path

import torch
from transformers import BertForSequenceClassification, BertTokenizer

BASE = Path(__file__).resolve().parent.parent  # hemao_scraper 根目录
MODEL_DIR = BASE / "data" / "out" / "bert_model"
LABEL_MAP_FILE = BASE / "data" / "out" / "label_map.json"
TEST_FILE = BASE / "data" / "processed" / "test_real.csv"

label_map = json.loads(LABEL_MAP_FILE.read_text("utf-8"))
inv = {v: k for k, v in label_map.items()}
tokenizer = BertTokenizer.from_pretrained(str(MODEL_DIR))
model = BertForSequenceClassification.from_pretrained(str(MODEL_DIR)).eval()
t0 = time.time()
print(f"模型加载完成 {time.time()-t0:.1f}s, 类别数={len(label_map)}")


def predict(text: str) -> tuple[str, list[tuple[str, float]]]:
    enc = tokenizer(text, max_length=128, padding="max_length",
                    truncation=True, return_tensors="pt")
    with torch.no_grad():
        logits = model(**enc).logits
        probs = torch.softmax(logits, dim=-1)[0].tolist()
    ranked = sorted(((inv[i], p) for i, p in enumerate(probs)),
                    key=lambda x: -x[1])
    return ranked[0][0], ranked


# ---------- 1. 测试报告引用的具体实例 ----------
print("\n" + "=" * 70)
print("A. 测试报告引用的具体实例(报告声称的结果 vs 真实模型)")
print("=" * 70)
cases = [
    ("网约车司机绕路并且态度恶劣", "旅游出行 99.8%(报告)", "共享出行"),
    ("干洗店把羊绒大衣洗坏了", "家居日用 99.3%(报告)", "本地生活"),
    ("4S店保养被强制搭售", "家居日用 86.3%(报告)", "汽车"),
    ("羽绒服跑绒", "电商平台 96.7%(报告)", "服饰鞋包"),
    ("直播买包", "电商平台 99.3%(报告)", "服饰鞋包"),
    ("家具尺寸不符", "房产家装 99.1%(报告)", "家居日用"),
    ("床垫塌陷", "房产家装 99.0%(报告)", "家居日用"),
    ("锅具掉渣", "电商平台 91.4%(报告)", "家居日用"),
    ("美发店会员卡", "医疗健康 95.8%(报告)", "本地生活"),
    ("外卖吃出异物", "本地生活 98.8%(报告)", "母婴食品"),
    ("直播打赏", "游戏 87.7%(报告)", "影音娱乐"),
]
for text, claimed, expect in cases:
    top, ranked = predict(text)
    p1, p2 = ranked[0][1], ranked[1][1]
    print(f"\n文本: {text}")
    print(f"  报告声称: {claimed}")
    print(f"  真实预测: {top} {p1:.1%}  | Top2 {ranked[1][0]} {p2:.1%}  | 差距 {p1-p2:.1%}  | 报告期望 {expect}")

# ---------- 2. 全量测试集统计 ----------
print("\n" + "=" * 70)
print("B. 真实测试集 test_real.csv 全量统计")
print("=" * 70)
rows = list(csv.DictReader(open(TEST_FILE, encoding="utf-8-sig", newline="")))
print(f"测试集样本数: {len(rows)}")

correct = 0
conf_all, conf_err = [], []
gap_all = []
t1 = time.time()
for r in rows:
    top, ranked = predict(r["text"])
    top_prob = ranked[0][1]
    conf_all.append(top_prob)
    gap_all.append(ranked[0][1] - ranked[1][1])
    if top == r["category"]:
        correct += 1
    else:
        conf_err.append(top_prob)
    if len(conf_all) % 200 == 0:
        print(f"  已跑 {len(conf_all)}/{len(rows)} ({time.time()-t1:.0f}s)")

n = len(rows)
acc = correct / n
mean_conf = sum(conf_all) / n
mean_conf_err = sum(conf_err) / len(conf_err) if conf_err else 0
gap_lt10 = sum(1 for g in gap_all if g < 0.10)
mean_gap = sum(gap_all) / n
err_high_conf = sum(1 for c in conf_err if c > 0.90)
print(f"\nTop-1 准确率: {acc:.4f} ({correct}/{n})   [bert_report.txt 声称 0.8540]")
print(f"平均 Top-1 置信度: {mean_conf:.4f}   [报告声称 0.983]")
print(f"错误样本数: {len(conf_err)}, 平均置信度: {mean_conf_err:.4f}   [报告声称 0.961]")
print(f"错误样本中置信度>90% 的: {err_high_conf}/{len(conf_err)}   [报告声称 10/12]")
print(f"Top1-Top2 差距<10% 的样本: {gap_lt10}/{n}   [报告声称 0 条]")
print(f"平均 Top1-Top2 差距: {mean_gap:.4f}")
