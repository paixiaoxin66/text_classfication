#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BERT 微调: bert-base-chinese 消费者投诉 18 类分类
================================================
在基线(TF-IDF+逻辑回归)基础上用预训练语言模型冲效果。

用法:
  uv run python train_bert.py                          # 训练+评估(自动检测GPU/CPU, 默认用数据流水线产物)
  uv run python train_bert.py --epochs 2 --batch-size 8   # 机器慢就调小
  uv run python train_bert.py --demo "京东快递不给我派件"    # 预测单条文本

默认数据(数据流水线 scripts/build_dataset.py 的产物):
  --train data/processed/train_augmented.csv   # 最终训练集(30000条)
  --val   data/processed/val_real.csv          # 验证集(854条, 100%真实)
  --test  data/processed/test_real.csv         # 测试集(877条, 100%真实)

输出(到 --out-dir):
  bert_model/             微调后的模型+tokenizer(HuggingFace格式)
  label_map.json          类别名<->数字ID
  bert_report.txt         测试集分类报告
  bert_confusion.png      混淆矩阵

说明:
  * 首次运行会自动下载 bert-base-chinese (~400MB), 需要网络
  * CPU 训练 8705条/3轮 约 2~4 小时; NVIDIA GPU 约 10~20 分钟
  * 依赖: torch transformers scikit-learn matplotlib
"""

from __future__ import annotations

import os

# 国内访问 HuggingFace 不稳定/超时 → 自动使用国内镜像 hf-mirror.com
# (若已在系统环境变量设置 HF_ENDPOINT, 以系统设置为准)
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import argparse
import csv
import json
import time
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score)
from torch.utils.data import DataLoader, Dataset
from transformers import (BertForSequenceClassification, BertTokenizer,
                          get_linear_schedule_with_warmup)

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None  # 没有 tqdm 时退化为普通循环, 不影响训练

SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)


def load_split(path: Path) -> tuple[list[str], list[str]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return [r["text"] for r in rows], [r["category"] for r in rows]


class ComplaintDataset(Dataset):
    def __init__(self, texts: list[str], labels: list[int], tokenizer, max_len: int):
        self.encodings = tokenizer(
            texts, max_length=max_len, padding="max_length",
            truncation=True, return_tensors="pt")
        self.labels = torch.tensor(labels)

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int):
        return {
            "input_ids": self.encodings["input_ids"][idx],
            "attention_mask": self.encodings["attention_mask"][idx],
            "labels": self.labels[idx],
        }


def plot_confusion(cm: np.ndarray, labels: list[str], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(16, 13))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels)), labels, rotation=90, fontsize=9)
    ax.set_yticks(range(len(labels)), labels, fontsize=9)
    ax.set_xlabel("预测类别")
    ax.set_ylabel("真实类别")
    ax.set_title("混淆矩阵(BERT, 测试集)")
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            if cm[i, j] > 0:
                ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=7)
    fig.colorbar(im)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description="BERT 微调: 消费者投诉分类")
    p.add_argument("--train", default="data/processed/train_augmented.csv")
    p.add_argument("--val", default="data/processed/val_real.csv")
    p.add_argument("--test", default="data/processed/test_real.csv")
    p.add_argument("--out-dir", default="data/out")
    p.add_argument("--model-name", default="", help="预训练模型: 本地目录 或 HF名称(默认自动检测本地 bert_model/)")
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--max-len", type=int, default=128)
    p.add_argument("--lr", type=float, default=2e-5)
    p.add_argument("--amp", action="store_true", help="启用混合精度fp16(GPU, 提速; 默认关闭更稳)")
    p.add_argument("--device", default="", help="cuda/cpu, 默认自动(cuda优先)")
    p.add_argument("--demo", default="", help="预测单条文本(需先训练)")
    args = p.parse_args()

    # 自动检测本地模型: 优先用下载好的 bert_model/, 否则用 HF 名称(走镜像)
    if not args.model_name:
        local = Path("bert_model/bert-base-chinese")
        if (local / "config.json").exists():
            args.model_name = str(local)
        else:
            args.model_name = "bert-base-chinese"
    print(f"预训练模型: {args.model_name}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # PyTorch CUDA 训练: 默认自动选(cuda优先), 可用 --device 强制指定
    if args.device:
        device = torch.device(args.device)
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cuda":
        gpu = torch.cuda.get_device_properties(0)
        print(f"GPU: {torch.cuda.get_device_name(0)}  (显存 {gpu.total_memory/1024**3:.1f} GB)")
    print(f"设备: {device}")

    # ---- 演示模式 ----
    if args.demo:
        model_dir = out_dir / "bert_model"
        tokenizer = BertTokenizer.from_pretrained(str(model_dir))
        model = BertForSequenceClassification.from_pretrained(str(model_dir)).to(device)
        label_map = json.loads((out_dir / "label_map.json").read_text("utf-8"))
        inv = {v: k for k, v in label_map.items()}
        enc = tokenizer(args.demo, max_length=args.max_len, padding="max_length",
                        truncation=True, return_tensors="pt").to(device)
        with torch.no_grad():
            logits = model(**enc).logits
            proba = torch.softmax(logits, dim=-1)[0]
        top = int(proba.argmax())
        print(f"文本: {args.demo}")
        print(f"预测类别: {inv[top]}  (置信度 {proba[top]:.2%})")
        for i in proba.argsort(descending=True)[:3].tolist():
            print(f"  {inv[i]:　<8} {proba[i]:.1%}")
        return

    # ---- 训练模式 ----
    X_train, y_train = load_split(Path(args.train))
    X_val, y_val = load_split(Path(args.val))
    X_test, y_test = load_split(Path(args.test))
    labels = sorted(set(y_train))
    label_map = {lbl: i for i, lbl in enumerate(labels)}
    n_class = len(labels)
    print(f"训练 {len(X_train)} / 验证 {len(X_val)} / 测试 {len(X_test)} / 类别 {n_class}")

    tokenizer = BertTokenizer.from_pretrained(args.model_name)
    model = BertForSequenceClassification.from_pretrained(
        args.model_name, num_labels=n_class).to(device)

    y_train_i = [label_map[y] for y in y_train]
    y_val_i = [label_map[y] for y in y_val]
    y_test_i = [label_map[y] for y in y_test]
    train_ds = ComplaintDataset(X_train, y_train_i, tokenizer, args.max_len)
    val_ds = ComplaintDataset(X_val, y_val_i, tokenizer, args.max_len)
    test_ds = ComplaintDataset(X_test, y_test_i, tokenizer, args.max_len)
    pin = device.type == "cuda"
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, pin_memory=pin)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size * 2, pin_memory=pin)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size * 2, pin_memory=pin)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    total_steps = len(train_loader) * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=int(total_steps * 0.1), num_training_steps=total_steps)

    # 混合精度: 默认关闭(fp32, 最稳)。GPU 上可用 --amp 开启(fp16 提速~2-3x)。
    # 若 fp16 出现 NaN loss, 自动回退 fp32 继续训练(不中断)。
    use_amp = args.amp and device.type == "cuda"
    scaler = torch.cuda.amp.GradScaler(enabled=use_amp)
    if use_amp:
        print("已启用混合精度 (AMP fp16), 遇 NaN 会自动回退 fp32")
    else:
        print("精度: fp32 (未启用 AMP, 最稳)")

    # 训练(每轮用验证集评估, 保存最优)
    best_f1, best_epoch = -1.0, -1
    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        model.train()
        total_loss = 0.0
        n_batch = 0
        pbar = tqdm(train_loader, desc=f"Epoch {epoch}/{args.epochs}",
                    unit="batch", ncols=100) if tqdm is not None else None
        for batch in (pbar if pbar is not None else train_loader):
            n_batch += 1
            batch = {k: v.to(device) for k, v in batch.items()}
            if use_amp:
                with torch.autocast(device_type=device.type, enabled=True):
                    outputs = model(**batch)
                    loss = outputs.loss
                if torch.isnan(loss) or torch.isinf(loss):
                    print(f"  ⚠️ fp16 loss={loss.item()}, 切换 fp32 继续")
                    use_amp = False
                    scaler = torch.cuda.amp.GradScaler(enabled=False)
            if not use_amp:
                outputs = model(**batch)
                loss = outputs.loss
            if use_amp:
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
            else:
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
            optimizer.zero_grad()
            total_loss += loss.item()
            if pbar is not None:
                pbar.set_postfix(loss=f"{total_loss/n_batch:.4f}")
        if pbar is not None:
            pbar.close()
        val_f1 = evaluate(model, val_loader, device, desc=f"验证(epoch {epoch})")
        print(f"✅ Epoch {epoch}/{args.epochs}: loss={total_loss/len(train_loader):.4f} "
              f"val macro-F1={val_f1:.4f} ({time.time()-t0:.0f}s)")
        if val_f1 > best_f1:
            best_f1, best_epoch = val_f1, epoch
            model.save_pretrained(out_dir / "bert_model")
            tokenizer.save_pretrained(out_dir / "bert_model")
    print(f"最优: epoch {best_epoch}, val macro-F1={best_f1:.4f}")

    # 测试集最终评估
    model = BertForSequenceClassification.from_pretrained(out_dir / "bert_model").to(device)
    y_true, y_pred = predict(model, test_loader, device, desc="测试中")
    acc = accuracy_score(y_true, y_pred)
    f1_macro = f1_score(y_true, y_pred, average="macro")
    print(f"测试集: 准确率={acc:.4f}  macro-F1={f1_macro:.4f}")

    report = (
        f"=== BERT 微调 ({args.model_name}, epochs={args.epochs}, bs={args.batch_size}) ===\n"
        f"数据: 训练{len(X_train)} 验证{len(X_val)} 测试{len(X_test)} 类别{n_class}\n"
        f"设备: {device}\n"
        f"准确率={acc:.4f}  macro-F1={f1_macro:.4f}\n\n"
        + classification_report(y_true, y_pred, target_names=labels, digits=4)
    )
    (out_dir / "bert_report.txt").write_text(report, "utf-8")
    print(report)

    cm = confusion_matrix(y_true, y_pred, labels=range(n_class))
    plot_confusion(cm, labels, out_dir / "bert_confusion.png")
    (out_dir / "label_map.json").write_text(
        json.dumps(label_map, ensure_ascii=False, indent=2), "utf-8")
    print(f"模型: {out_dir/'bert_model'}  报告: {out_dir/'bert_report.txt'}  混淆矩阵: {out_dir/'bert_confusion.png'}")


def evaluate(model, loader, device, desc: str = "评估") -> float:
    y_true, y_pred = predict(model, loader, device, desc)
    return f1_score(y_true, y_pred, average="macro")


def predict(model, loader, device, desc: str = "评估") -> tuple[list, list]:
    model.eval()
    y_true, y_pred = [], []
    it = tqdm(loader, desc=desc, unit="batch", ncols=90) if tqdm is not None else loader
    with torch.no_grad():
        for batch in it:
            batch = {k: v.to(device) for k, v in batch.items()}
            logits = model(**batch).logits
            y_true.extend(batch["labels"].cpu().tolist())
            y_pred.extend(logits.argmax(dim=-1).cpu().tolist())
    return y_true, y_pred


if __name__ == "__main__":
    main()
