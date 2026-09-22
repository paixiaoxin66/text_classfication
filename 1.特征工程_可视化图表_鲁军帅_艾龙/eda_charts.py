# -*- coding: utf-8 -*-
"""EDA 可视化(答辩PPT用) —— 全部基于真实数据
输出: data/eda/
  1. eda_length_hist.png     文本长度直方图(真实6893)
  2. eda_category_dist.png   18类分布对比(真实6893 vs 增强后训练集30000)
  3. eda_top20_words.png     高频词Top20(字符bigram, 真实文本)
"""
import csv
import re
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

PINK = "#F45B95"
PURPLE = "#8E6BE8"
TEAL = "#38B7A5"
LIGHT = "#FFC9DE"
OUT = Path("data/eda")
OUT.mkdir(parents=True, exist_ok=True)


def load(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


real = load("data/processed/train_real.csv")
aug = load("data/processed/train_augmented.csv")

# ---------- 1. 文本长度直方图 ----------
lens = np.array([len(r["text"]) for r in real])
q99 = int(np.percentile(lens, 99))
fig, ax = plt.subplots(figsize=(10, 5.2), dpi=150)
ax.hist(lens, bins=40, range=(0, q99), color=LIGHT, edgecolor="white", alpha=0.95)
ax.axvline(lens.mean(), color=PINK, lw=2.2, ls="--", label=f"均值 {lens.mean():.0f} 字")
ax.axvline(np.median(lens), color=PURPLE, lw=2.2, ls="-.", label=f"中位数 {np.median(lens):.0f} 字")
ax.set_title(f"投诉文本长度分布（真实数据 N={len(lens):,} 条，截断至 99 分位 {q99} 字）",
             fontsize=13, pad=12)
ax.set_xlabel("文本长度（字符数）", fontsize=11)
ax.set_ylabel("样本数", fontsize=11)
ax.legend(fontsize=10, framealpha=0.9)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
fig.savefig(OUT / "eda_length_hist.png")
plt.close(fig)
print(f"[1] 长度直方图: 均值{lens.mean():.1f} 中位数{np.median(lens):.0f} 最长{lens.max()} → {OUT/'eda_length_hist.png'}")

# ---------- 2. 18类分布(真实 vs 增强后) ----------
real_c = Counter(r["category"] for r in real)
aug_c = Counter(r["category"] for r in aug)
cats = [c for c, _ in real_c.most_common()]
n_real = [real_c[c] for c in cats]
n_aug = [aug_c[c] for c in cats]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6.2), dpi=150)
y = np.arange(len(cats))
for ax, data, title, color in [
    (ax1, n_real, f"真实样本分布（N={sum(n_real):,}）", PINK),
    (ax2, n_aug, f"增强后训练集分布（N={sum(n_aug):,}）", PURPLE),
]:
    ax.barh(y, data, color=color, alpha=0.88, height=0.62)
    ax.set_yticks(y, cats, fontsize=10)
    ax.invert_yaxis()
    ax.set_title(title, fontsize=12.5, pad=10)
    ax.set_xlabel("样本数", fontsize=10)
    for yi, v in enumerate(data):
        ax.text(v + max(data) * 0.008, yi, f"{v:,}", va="center", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", alpha=0.25)
fig.suptitle("18 类投诉类别分布：数据增强前后的均衡化效果", fontsize=14, y=1.0)
fig.tight_layout()
fig.savefig(OUT / "eda_category_dist.png", bbox_inches="tight")
plt.close(fig)
print(f"[2] 类别分布对比图 → {OUT/'eda_category_dist.png'}")

# ---------- 3. 高频词 Top20(字符bigram) ----------
STOP = set("的了是我你他在有和就不人都也还很这那与及或对为等第个上下中于么呢吧啊哦呀什么如何哪些这这这些那些都可以要不没出在到从给把被让向跟随自己我们你们他们她们它们")
STOP |= set(" ，。、！？；：“”‘’（）《》【】—…·％%0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ年月日小时分秒元块钱")

bigram_cnt = Counter()
for r in real:
    t = re.sub(r"[^\u4e00-\u9fff]", " ", r["text"])
    chars = [c for c in t if c and c not in STOP]
    bigram_cnt.update(a + b for a, b in zip(chars, chars[1:]))

top = bigram_cnt.most_common(20)[::-1]  # 升序, 让最大在顶部
words = [w for w, _ in top]
cnts = [c for _, c in top]

fig, ax = plt.subplots(figsize=(10, 6.2), dpi=150)
bars = ax.barh(words, cnts, color=[TEAL if i % 2 else PINK for i in range(len(top))], alpha=0.9, height=0.62)
for i, v in enumerate(cnts):
    ax.text(v + max(cnts) * 0.006, i, f"{v:,}", va="center", fontsize=9)
ax.set_title(f"投诉文本高频词 Top20（字符二元组，真实数据 N={len(real):,}）", fontsize=13, pad=12)
ax.set_xlabel("出现次数", fontsize=11)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="x", alpha=0.25)
fig.tight_layout()
fig.savefig(OUT / "eda_top20_words.png")
plt.close(fig)
print(f"[3] 高频词Top20 → {OUT/'eda_top20_words.png'}")
print("Top10:", [f"{w}({c})" for w, c in bigram_cnt.most_common(10)])
