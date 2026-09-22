# -*- coding: utf-8 -*-
"""独立复算: 验证 EDA 图表数字是否来自真实数据(与 eda_charts.py 无关的第二套计算)"""
import csv
import re
from collections import Counter

def load(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

raw = load("data/raw/hemao_complaints.csv")          # 原始爬取(未动)
real = load("data/processed/train_real.csv")          # EDA 用: 真实训练集
aug = load("data/processed/train_augmented.csv")      # 增强后训练集
cleaned = load("data/processed/cleaned_complaints.csv")

print("=" * 60)
print("一、数据血缘")
print("=" * 60)
print(f"原始爬取 hemao_complaints.csv      : {len(raw):,} 条 (只读未改)")
print(f"清洗后   cleaned_complaints.csv    : {len(cleaned):,} 条")
print(f"真实训练集 train_real.csv          : {len(real):,} 条 (EDA 长度图/词频图/分布图左半)"
      f"\n增强后训练集 train_augmented.csv   : {len(aug):,} 条 (分布图右半, 已标注'增强后')")

print("\n" + "=" * 60)
print("二、真实训练集样本抽查(是否像真实投诉)")
print("=" * 60)
for r in real[:3]:
    print(f"[{r['category']}] {r['text'][:50]}…")

print("\n" + "=" * 60)
print("三、长度指标独立复算")
print("=" * 60)
lens = [len(r["text"]) for r in real]
import statistics
mean = statistics.fmean(lens); med = statistics.median(lens)
print(f"图表: 均值212.1 中位数156 最长1041")
print(f"复算: 均值{mean:.1f} 中位数{med:.0f} 最长{max(lens)}")
print(f"→ {'一致 ✓' if abs(mean-212.1)<0.5 and med==156 and max(lens)==1041 else '不一致 ✗'}")

print("\n" + "=" * 60)
print("四、18类分布独立复算(真实集)")
print("=" * 60)
rc = Counter(r["category"] for r in real)
ac = Counter(r["category"] for r in aug)
for c in ["本地生活", "电商平台", "母婴食品", "教育"]:
    print(f"  {c}: 真实={rc[c]:,}  增强后={ac[c]:,}")
print(f"  真实集合计 {sum(rc.values()):,} / 增强集合计 {sum(ac.values()):,} (图表: 6,893 / 30,000)")

print("\n" + "=" * 60)
print("五、高频词(字符bigram)独立复算 vs 图表")
print("=" * 60)
STOP = set("的了是我你他在有和就不人都也还很这那与及或对为等第个上下中于么呢吧啊哦呀什么如何哪些这这些那些都可以要不没出在到从给把被让向跟随自己我们你们他们她们它们")
STOP |= set(" ，。、！？；：“”‘’（）《》【】—…·％%0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ年月日小时分秒元块钱")
bc = Counter()
for r in real:
    t = re.sub(r"[^\u4e00-\u9fff]", " ", r["text"])
    ch = [c for c in t if c and c not in STOP]
    bc.update(a + b for a, b in zip(ch, ch[1:]))
for w in ["平台", "客服", "退款", "商家"]:
    print(f"  {w}: 图表={ {'平台':5660,'客服':4992,'退款':4958,'商家':4028}[w]:,}  复算={bc[w]:,}  "
          f"{'✓' if bc[w]=={'平台':5660,'客服':4992,'退款':4958,'商家':4028}[w] else '✗'}")

print("\n" + "=" * 60)
print("六、与原始数据交叉验证(真实样本应能追溯到原始投诉)")
print("=" * 60)
raw_ids = {r["id"] for r in raw}
real_ids = {r["id"] for r in real if "id" in r and r["id"]}
if real_ids:
    hit = len(real_ids & raw_ids)
    print(f"  train_real 中带 id 的样本 {len(real_ids):,} 条, 命中原始爬取 id {hit:,} 条 "
          f"({hit/len(real_ids)*100:.1f}%)")
else:
    print("  train_real 无 id 字段(已脱敏处理), 改用文本抽样比对:")
    raw_texts = {r["text"][:40] for r in raw}
    hit = sum(1 for r in real[:500] if r["text"][:40] in raw_texts)
    print(f"  前500条中与原始文本开头40字完全一致的: {hit} 条 ({hit/5:.0f}%)")
