# -*- coding: utf-8 -*-
"""清洗前后对比图 —— 原始 vs 清洗后(数量/重复率/标签噪声)
输出: data/eda/eda_cleaning_compare.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

PINK = "#F45B95"
PURPLE = "#8E6BE8"
LIGHT = "#FFC9DE"
OUT = "data/eda/eda_cleaning_compare.png"

fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.4), dpi=150)

# ---------- 面板1: 样本数量 ----------
ax = axes[0]
names = ["原始", "清洗后"]
vals = [9043, 8950]
bars = ax.bar(names, vals, color=[LIGHT, PINK], width=0.5)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + 90, f"{v:,}", ha="center", fontsize=11, fontweight="bold")
ax.set_title("① 样本数量", fontsize=12.5, pad=8)
ax.set_ylabel("条数", fontsize=10)
ax.annotate(f"移除 {9043-8950} 条\n(-1.0%)", xy=(1, 8950), xytext=(1.28, 9200),
            fontsize=9, color="#C0487F", ha="center",
            arrowprops=dict(arrowstyle="->", color="#C0487F", lw=1.4))
ax.set_ylim(0, 10100)
ax.spines[["top", "right"]].set_visible(False)

# ---------- 面板2: 完全重复率 ----------
ax = axes[1]
vals2 = [1.39, 0.00]
bars = ax.bar(names, vals2, color=[LIGHT, PINK], width=0.5)
for b, v in zip(bars, vals2):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.06, f"{v:.2f}%", ha="center", fontsize=11, fontweight="bold")
ax.set_title("② 完全重复率", fontsize=12.5, pad=8)
ax.set_ylabel("占比", fontsize=10)
ax.annotate("126 行重复\n→ 0 行", xy=(1, 0.0), xytext=(1.28, 1.6),
            fontsize=9, color="#C0487F", ha="center",
            arrowprops=dict(arrowstyle="->", color="#C0487F", lw=1.4))
ax.set_ylim(0, 1.85)
ax.spines[["top", "right"]].set_visible(False)

# ---------- 面板3: 标签噪声 ----------
ax = axes[2]
groups = ["数字标签\n(未映射ID)", "其他/未分类\n(混合噪声)"]
before = [16, 338]
after = [0, 325]
x = [0, 1]
w = 0.3
b1 = ax.bar([i - w / 2 for i in x], before, width=w, color=LIGHT, label="清洗前")
b2 = ax.bar([i + w / 2 for i in x], after, width=w, color=PURPLE, label="清洗后")
for b, v in zip(list(b1) + list(b2), before + after):
    ax.text(b.get_x() + b.get_width() / 2, v + 8, f"{v}", ha="center", fontsize=10)
ax.set_xticks(x, groups, fontsize=10)
ax.set_title("③ 标签噪声清理", fontsize=12.5, pad=8)
ax.set_ylabel("条数", fontsize=10)
ax.set_ylim(0, 420)
ax.legend(fontsize=9, loc="upper right")
ax.spines[["top", "right"]].set_visible(False)

fig.suptitle("数据清洗前后对比（黑猫投诉 9,043 条原始数据）", fontsize=14, y=1.02)
fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
print(f"已生成: {OUT}")
