#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据增强: 只对 Train(真实) 做增强, 生成 30000 条级训练集
============================================
两条路线:
  1) LLM 语义保持改写 (优先, 需配置 LLM_BASE_URL/LLM_API_KEY/LLM_MODEL)
  2) 规则/领域词增强 (无 LLM 时自动退化, 纯标准库可跑)

规则增强方法(均为语义保持):
  * 领域同义词替换(退款→退钱/拒绝退款…)
  * 逗号分隔诉求列表重排(不改变事实)
  * 程度/持续性副词插入(一直不予退款 → 一直不予退款)
  不改变: 金额/时间/品牌/产品/投诉对象; 不使用随机删除/随机交换。

类别均衡预算(按真实样本数分带):
  A <200 : 严重少数, 最多增强
  B 200-400 : 中等少数, 较多增强
  C 400-700 : 正常, 轻量增强
  D >700 : 多数, 尽量少增强
  --target-size 驱动目标总量, --aug-scale 可手动放大。

断点续跑: 每次处理后把结果追加到输出CSV; --resume 时跳过已生成的原始样本。

用法:
  python scripts/augment_dataset.py --train data/processed/train_real.csv \
      --target-size 30000 --seed 42
  python scripts/augment_dataset.py --resume --mode rule   # 中断后继续
  python scripts/augment_dataset.py --limit-originals 100  # 小规模测试
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import os
import random
import re
import time
import urllib.request
from collections import Counter
from pathlib import Path

from clean_complaints import load_rows, write_csv


def stable_id(rid: str) -> int:
    """确定性字符串哈希(避免 PYTHONHASHSEED 随机化破坏可复现性)。"""
    return int(hashlib.md5(rid.encode("utf-8")).hexdigest()[:8], 16)


# ---------------- 数字保护: 增强期间金额/数字不可被破坏 ----------------
NUM_TOKEN = re.compile(r"(?:¥|￥)?\d+(?:\.\d+)?(?:元|块|块钱|rmb|RMB|万|亿|折|天|日|号|月|年|小时|分钟|秒|公里|米|个|台|件|次|期|人|岁|成|%|％)?")


def protect_numbers(text: str) -> tuple[str, dict]:
    placeholders: dict[str, str] = {}

    def repl(m: re.Match) -> str:
        tok = f"__NUM{len(placeholders)}__"
        placeholders[tok] = m.group(0)
        return tok

    return NUM_TOKEN.sub(repl, text), placeholders


def restore_numbers(text: str, placeholders: dict) -> str:
    for tok, val in placeholders.items():
        text = text.replace(tok, val)
    return text

# ---------------- LLM 配置(从环境变量或 .env 读取, 不硬编码 Key) ----------------
ENV_KEYS = ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL")


def load_llm_config() -> dict:
    """优先读环境变量, 其次读项目根目录 .env 文件。"""
    cfg = {k: os.environ.get(k) for k in ENV_KEYS}
    if not cfg["LLM_BASE_URL"]:
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text("utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    k = k.strip()
                    if k in ENV_KEYS:
                        cfg[k] = v.strip().strip('"').strip("'")
    if cfg["LLM_BASE_URL"] and cfg["LLM_API_KEY"] and cfg["LLM_MODEL"]:
        return cfg
    return {}


# ---------------- 领域同义词词典(语义保持, 金额/品牌不动) ----------------
SYNONYM_PAIRS = [
    ("不予退款", ["拒绝退款", "不同意退款", "拒不退款", "不答应退款", "不给退款"]),
    ("退款", ["退钱", "退回款项", "返还费用"]),
    ("客服", ["售后客服", "平台客服", "客服人员", "售后人员"]),
    ("商家", ["卖家", "店铺", "商户", "店家"]),
    ("无法", ["不能", "没法", "无法正常"]),
    ("联系不到", ["联系不上", "联系不上对方", "找不到"]),
    ("虚假宣传", ["夸大宣传", "宣传不实", "虚假广告"]),
    ("质量", ["品质", "质量问题"]),
    ("服务态度", ["服务态度", "态度"]),
    ("处理", ["解决", "跟进处理"]),
    ("扣款", ["扣费", "扣钱", "划扣"]),
    ("赔偿", ["赔付", "补偿"]),
    ("发货", ["发货", "配送"]),
    ("逾期", ["超期", "过了期限"]),
    ("拖延", ["拖延", "迟迟不办"]),
    ("投诉", ["反映问题", "投诉举报"]),
    ("订单", ["订单", "这笔订单"]),
    ("商家拒不", ["商家拒绝", "卖家拒不"]),
    ("一直不", ["始终不", "始终没有"]),
    ("商品", ["商品", "货物", "货品"]),
]
# 注意: 部分"同义词"实为同义短语; 替换是随机的, 每次只替换部分命中词, 保证多样性。
SYNONYM_LIST = [(k, vs) for k, vs in SYNONYM_PAIRS]


def synonym_replace(text: str, rng: random.Random) -> str:
    """替换 2-4 处领域同义词(改写力度更大, 避免近复制)。"""
    present = [k for k, _ in SYNONYM_LIST if k in text]
    if not present:
        return text
    k_n = min(len(present), rng.randint(2, 4))
    keys = rng.sample(present, k_n)
    t = text
    for k in keys:
        idx = t.find(k)
        if idx < 0:
            continue
        vs = [v for v in dict(SYNONYM_LIST)[k] if v != k]
        if not vs:
            continue
        t = t[:idx] + rng.choice(vs) + t[idx + len(k):]
    return t


def reorder_issue_list(text: str, rng: random.Random) -> str:
    """对逗号分隔的 2-5 个完整短诉求/问题片段重排(语义不变)。
    匹配整段逗号子句(不截断中文字符串, 避免破坏数字/占位符)。"""
    m = re.search(r"([^，。；\n]{2,80}(?:，[^，。；\n]{2,80}){1,4})", text)
    if not m:
        return text
    seg = m.group(1)
    parts = [s for s in seg.split("，") if s.strip()]
    if len(parts) < 2 or len(parts) > 5:
        return text
    rng.shuffle(parts)
    return text[:m.start()] + "，".join(parts) + text[m.end():]


ADV_BEFORE = ["一直", "总是", "反复", "始终"]
ADV_PATTERN = re.compile(r"(?<![一直总是反复始终])(不[予退换货给返]|不处理|不发货|不解决|无法|拒不|拖延|迟迟不)")


def insert_adverb(text: str, rng: random.Random) -> str:
    """在否定/拖延短语前插入程度副词(如: 不予退款→一直不予退款)。"""
    m = ADV_PATTERN.search(text)
    if not m:
        return text
    adv = rng.choice(ADV_BEFORE)
    return text[:m.start()] + adv + m.group(1) + text[m.end():]


def swap_sentences(text: str, rng: random.Random) -> str:
    """交换两个句子的顺序(语义保持, 显著提升差异度)。"""
    parts = [p for p in re.split(r"(?<=[。！？!?])", text) if p.strip()]
    if len(parts) < 2:
        return text
    i, j = rng.sample(range(len(parts)), 2)
    parts[i], parts[j] = parts[j], parts[i]
    return "".join(parts)


# ---------------- 类别均衡预算 ----------------
# (样本数上界, 目标倍数, 每原始样本最大变体数)
BAND_A, BAND_B, BAND_C, BAND_D = (200, 20, 12), (400, 12, 10), (700, 6, 8), (float("inf"), 3, 6)


def per_class_target(real: int, scale: float) -> int:
    for upper, mult, _ in (BAND_A, BAND_B, BAND_C, BAND_D):
        if real < upper:
            return max(real, min(int(1500 * scale), int(real * mult * scale)))
    return real


def compute_plan(real_counts: dict, target_size: int) -> tuple[dict, float]:
    """按 target-size 自动推算每个类别应增强多少(scale 自动缩放)。"""
    plan = {}
    scale = 1.0
    for s in [x / 100 for x in range(100, 301, 5)]:
        total = sum(per_class_target(c, s) for c in real_counts.values())
        if total >= target_size:
            scale = s
            break
    for cat, real in real_counts.items():
        for upper, _, max_var in (BAND_A, BAND_B, BAND_C, BAND_D):
            if real < upper:
                target = per_class_target(real, scale)
                aug = max(0, min(target - real, real * max_var))
                plan[cat] = {"real": real, "target": target, "aug": aug, "max_var": max_var}
                break
    return plan, scale


# ---------------- 规则增强生成 ----------------
def generate_variants_rule(text: str, rng: random.Random, n: int) -> list[str]:
    ops = [synonym_replace, reorder_issue_list, insert_adverb, swap_sentences]
    # 数字保护: 增强期间金额/日期/数量等以占位符形式存在, 操作无法直接破坏
    protected, placeholders = protect_numbers(text)
    digits_orig = sorted(re.findall(r"\d+", text))
    out: list[str] = []
    seen: set[str] = set()
    attempts = 0
    while len(out) < n and attempts < n * 15:
        attempts += 1
        # 每变体叠加 2-4 种操作, 保证与原文本差异足够大
        k = rng.randint(2, 4)
        t = protected
        for op in rng.sample(ops, min(k, len(ops))):
            t = op(t, rng)
        t = restore_numbers(t, placeholders)
        # 兜底校验: 恢复后数字序列必须与原文完全一致, 任何损伤都丢弃
        if sorted(re.findall(r"\d+", t)) != digits_orig:
            continue
        t = t.strip()
        if t and t != text and t not in seen:
            seen.add(t)
            out.append(t)
    return out


# ---------------- LLM 增强 ----------------
LLM_PROMPT = (
    "你是一名消费者投诉数据增强助手。请对下面的消费者投诉文本进行语义保持式改写。\n"
    "要求：\n"
    "1. 保持投诉类别不变\n"
    "2. 保持原始投诉事实不变\n"
    "3. 不新增原文不存在的事实\n"
    "4. 不删除核心投诉问题\n"
    "5. 不改变金额、时间、品牌、产品、投诉对象\n"
    "6. 使用自然的中文消费者投诉表达\n"
    "7. 改写后必须仍然像真实消费者投诉\n"
    "8. 不要添加解释\n"
    "9. 只输出改写后的投诉文本, 每行一条\n\n"
    "原始类别：{category}\n"
    "原始投诉：{text}"
)
LLM_META_WORDS = ["作为AI", "作为人工智能", "根据您的要求", "以下是", "希望我的回答",
                  "作为一名", "我不能", "我无法", "抱歉", "很高兴", "谢谢"]


def llm_rewrite(cfg: dict, text: str, category: str, n: int) -> list[str]:
    """调用 OpenAI-compatible 接口, 返回 n 条改写。带重试。"""
    payload = {
        "model": cfg["LLM_MODEL"],
        "messages": [{"role": "user", "content": LLM_PROMPT.format(category=category, text=text)}],
        "temperature": 0.8,
        "max_tokens": 1024,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        cfg["LLM_BASE_URL"], data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {cfg['LLM_API_KEY']}"})
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            content = body["choices"][0]["message"]["content"]
            lines = [ln.strip().lstrip("0123456789.、)） ").strip()
                     for ln in content.splitlines() if ln.strip()]
            lines = [ln for ln in lines if not any(w in ln for w in LLM_META_WORDS)]
            return lines[:n]
        except Exception as e:
            time.sleep(attempt * 5)   # 退避重试
    return []


# ---------------- 主流程 ----------------
def build_rows(original: dict, variants: list[str], method: str, rng: random.Random) -> list[dict]:
    rows = []
    for i, v in enumerate(variants):
        rows.append({
            "src_id": original["id"], "category": original["category"],
            "text": v, "aug_method": method,
            "is_aug": "1", "variant_idx": i,
        })
    return rows


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="训练集增强(LLM/规则)")
    p.add_argument("--train", default="data/processed/train_real.csv")
    p.add_argument("--output", default="data/augmentation/generated_raw.csv")
    p.add_argument("--failures", default="data/augmentation/failures.jsonl")
    p.add_argument("--target-size", type=int, default=30000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--mode", choices=["auto", "llm", "rule"], default="auto")
    p.add_argument("--aug-scale", type=float, default=0.0,
                   help="手动增强缩放系数(0=按target-size自动推算)")
    p.add_argument("--limit-originals", type=int, default=0,
                   help="只增强前N个原始样本(测试用)")
    p.add_argument("--resume", action="store_true", help="断点续跑(跳过已生成的src_id)")
    p.add_argument("--batch-size", type=int, default=10, help="LLM并发批大小")
    p.add_argument("--max-workers", type=int, default=4, help="LLM并发数")
    p.add_argument("--llm-min-interval", type=float, default=0.5, help="LLM批次最小间隔秒")
    args = p.parse_args(argv)

    train_rows = load_rows(Path(args.train))
    real_counts = Counter(r["category"] for r in train_rows)
    plan, scale = compute_plan(dict(real_counts), args.target_size)
    if args.aug_scale > 0:
        scale = args.aug_scale
        plan, _ = compute_plan(dict(real_counts), int(sum(
            per_class_target(c, scale) for c in real_counts.values())))
    print(f"增强计划 (scale={scale:.2f}, 目标总train={args.target_size}):")
    for cat, info in sorted(plan.items(), key=lambda x: -x[1]["aug"]):
        print(f"  {cat}: 真实{info['real']} → 目标{info['target']} (增{info['aug']}, 每原样≤{info['max_var']}变体)")

    cfg = load_llm_config()
    mode = args.mode
    if mode == "auto":
        mode = "llm" if cfg else "rule"
    print(f"增强模式: {mode}" + (f" (LLM: {cfg.get('LLM_MODEL')})" if mode == "llm" else " (规则增强, 无LLM)"))

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done_src = set()
    if args.resume and out_path.exists():
        for r in load_rows(out_path):
            done_src.add(r["src_id"])
        print(f"断点续跑: 已跳过 {len(done_src)} 个已生成的原始样本")

    if args.limit_originals:
        train_rows = train_rows[: args.limit_originals]
        print(f"测试模式: 仅处理前 {len(train_rows)} 个原始样本")

    # 每次追加写, 兼作 checkpoint; 非 --resume 时重建文件
    file_mode = "a" if args.resume else "w"
    file_handle = open(out_path, file_mode, newline="", encoding="utf-8-sig")
    writer = csv.DictWriter(file_handle, fieldnames=["src_id", "category", "text",
                                                     "aug_method", "is_aug", "variant_idx"])
    if file_mode == "w":
        writer.writeheader()

    processed = failed = 0
    gen_total = 0
    t_start = time.time()
    with open(Path(args.failures), "a", encoding="utf-8") as f_fail:
        for row in train_rows:
            cat, text, rid = row["category"], row["text"], row["id"]
            if rid in done_src:
                continue
            aug_n = plan.get(cat, {}).get("aug", 0)
            if aug_n <= 0:
                continue
            max_var = plan.get(cat, {}).get("max_var", 10)
            per_orig = min(aug_n, max_var)
            rng = random.Random((args.seed * 1_000_003 + stable_id(rid)) % (2 ** 32))  # 可复现
            if mode == "llm":
                variants = llm_rewrite(cfg, text, cat, per_orig)
            else:
                variants = generate_variants_rule(text, rng, per_orig)
            if not variants:
                failed += 1
                f_fail.write(json.dumps({"id": rid, "category": cat}, ensure_ascii=False) + "\n")
                continue
            writer.writerows(build_rows(row, variants, mode, rng))
            file_handle.flush()
            processed += 1
            gen_total += len(variants)
            if processed % 200 == 0:
                el = time.time() - t_start
                print(f"  已处理 {processed} 个原始样本, 生成 {gen_total} 条, 用时 {el:.0f}s")
            if mode == "llm":
                time.sleep(args.llm_min_interval)
    file_handle.close()

    n_rows = 0
    if out_path.exists():
        n_rows = len(load_rows(out_path))
    print(f"完成: 处理 {processed} 个原始样本, 失败 {failed}")
    print(f"增强原始输出: {out_path} 共 {n_rows} 行")
    print("下一步: python scripts/filter_augmented.py")


if __name__ == "__main__":
    main()
