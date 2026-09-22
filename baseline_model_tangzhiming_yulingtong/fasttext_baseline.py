# -*- coding: utf-8 -*-
"""FastText 基线 —— 同一真实测试集(877), 与 NB/LR/SVM/RF/BERT 对比
FastText 内置子词(char n-gram), 中文无需分词
"""
import csv
import os
import time

import fasttext
from sklearn.metrics import accuracy_score, f1_score

TMP = "data/tmp_fasttext"
os.makedirs(TMP, exist_ok=True)


def dump(p, rows):
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            # 文本内换行转空格(fasttext 按行读)
            text = " ".join(r["text"].split())
            f.write(f"__label__{r['category']} {text}\n")


def load(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


train = load("data/processed/train_augmented.csv")
val = load("data/processed/val_real.csv")
test = load("data/processed/test_real.csv")
dump(f"{TMP}/train.txt", train)
dump(f"{TMP}/val.txt", val)
dump(f"{TMP}/test.txt", test)
print(f"train {len(train)} / val {len(val)} / test {len(test)}", flush=True)

t0 = time.time()
model = fasttext.train_supervised(
    f"{TMP}/train.txt",
    lr=0.5, epoch=25, wordNgrams=2, dim=100,
    minn=2, maxn=4, thread=4, seed=42, verbose=2,
)
train_sec = time.time() - t0
model.save_model("data/out/fasttext_model.bin")
print(f"FastText 训练完成, 用时 {train_sec:.1f}s -> data/out/fasttext_model.bin", flush=True)

# 测试集评估
t0 = time.time()
y_true, y_pred = [], []
with open(f"{TMP}/test.txt", encoding="utf-8") as f:
    lines = [ln.rstrip("\n") for ln in f if ln.strip()]
for ln in lines:
    parts = ln.split(" ", 1)
    y_true.append(parts[0].replace("__label__", ""))
    text = parts[1] if len(parts) > 1 else ""
    lab, _ = model.predict(text, k=1)
    y_pred.append(lab[0].replace("__label__", ""))

acc = accuracy_score(y_true, y_pred)
macro = f1_score(y_true, y_pred, average="macro")
weighted = f1_score(y_true, y_pred, average="weighted")
print(f"\nFastText(默认超参 epoch=25) 测试集: acc={acc:.4f} macroF1={macro:.4f} weightedF1={weighted:.4f}")
print(f"推理用时 {time.time()-t0:.1f}s ({len(y_true)} 条)")
