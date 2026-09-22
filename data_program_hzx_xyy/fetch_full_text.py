#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取投诉详情页全文, 补全被平台截断的 summary
============================================================
背景: 黑猫 feed 接口的 summary 字段被平台按 ~445 字节预算截断并补 "..."。
      实测 9043 条中约 4004 条(44%) 以省略号结尾且字节聚在 438-445B —— 全部被截断。
      完整正文只在详情页 https://tousu.sina.cn/complaint/view/{id}/ 上。

本脚本:
  1) 识别"疑似截断"行: 以省略号结尾(字节>=350, 截断簇) 或 (>=140字且词中截断)
  2) 抓详情页 HTML, 多策略提取全文
  3) 输出 data/raw/full_text_patch.csv (id, full_text, ...) + 失败日志

用法(需在能联网的本机):
  # 第0步(推荐): 探测详情接口/页面结构, 确认提取效果
  uv run python scripts/fetch_full_text.py --probe 17399929650
  # 第1步: 试跑 5 条并保存 HTML 样例
  uv run python scripts/fetch_full_text.py --limit 5 --debug-samples 5 --delay 1.5
  # 第2步: 全量抓疑似截断行(约4000条, delay 1.5 约 1.7 小时)
  uv run python scripts/fetch_full_text.py --delay 1.5
  # 第3步: 回填 → 重建(见 apply_full_text.py 与 build_dataset.py --raw)

说明:
  * 提取策略见 EXTRACT_PATTERNS; 页面结构变化导致提取为空时, 用
    data/debug/detail_pages/*.html 样例调整正则
  * 失败行保持原 summary, 不丢数据; 可 --resume 续跑(已成功的跳过)
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://tousu.sina.cn/complaint/view/{}/"

# 候选详情 JSON 接口(用于 --probe 探测, {id} 会被替换)
API_CANDIDATES = [
    "https://tousu.sina.cn/api/detail?id={id}",
    "https://tousu.sina.cn/api/detail?sn={id}",
    "https://tousu.sina.cn/api/complaint/detail?id={id}",
    "https://tousu.sina.cn/api/index/detail?id={id}",
    "https://tousu.sina.cn/api/feed/detail?id={id}",
]

# 详情页提取策略: (正则, 说明)。按顺序尝试, 取第一个命中。
# 实测黑猫详情页(H5)结构: 正文在 <div class="m-complaint-des4"><p>全文</p></div>
EXTRACT_PATTERNS = [
    # 1) 正文容器 m-complaint-des4 内的首个 <p> (最精确)
    (r'<div[^>]*class="m-complaint-des4"[^>]*>[\s\S]*?<p[^>]*>([\s\S]*?)</p>', "正文 des4>p"),
    # 2) 正文容器整体文本
    (r'<div[^>]*class="m-complaint-des4"[^>]*>([\s\S]*?)</div>', "正文 des4 div"),
    # 3) 标题 h1.m-complaint-title (正文缺失时兜底)
    (r'<h1[^>]*class="m-complaint-title"[^>]*>([\s\S]*?)</h1>', "标题 h1"),
    # 4) 页面内嵌 JSON
    (r'"content"\s*:\s*"((?:[^"\\]|\\.)*)"', "JSON content 字段"),
    (r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;', "INITIAL_STATE JSON"),
    (r'<div[^>]*class="[^"]*content[^"]*"[^>]*>([\s\S]*?)</div>', "content div"),
    (r'<p[^>]*>([\s\S]*?)</p>', "p 标签"),
]

UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1")


def fetch(url: str, timeout: float = 15.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def html_to_text(html: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", html)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_full_text(page_html: str) -> str:
    """多策略提取正文; 返回空串表示没提出来。"""
    # 无效页防护: 黑猫的"页面不存在"提示页直接判失败
    if "页面不存在" in page_html or "3秒后将返回黑猫投诉首页" in page_html:
        return ""
    for pat, _name in EXTRACT_PATTERNS:
        m = re.search(pat, page_html)
        if not m:
            continue
        raw = m.group(1)
        if pat.startswith('r\'"content"') or "INITIAL_STATE" in pat:
            raw = raw.replace("\\n", "\n").replace("\\\"", '"').replace("\\\\", "\\")
        else:
            raw = re.sub(r"<[^>]+>", " ", raw)
        text = html_to_text(raw) if "<" in raw else raw.strip()
        text = html.unescape(text)
        if len(text) >= 30:
            return text
    body = html_to_text(page_html)
    blocks = [b.strip() for b in re.split(r"[。！？!?]", body) if len(b.strip()) >= 20]
    if blocks:
        return "。".join(blocks[:10]) + "。"
    return ""


def is_suspicious(summary: str, byte_threshold: int = 350) -> bool:
    """疑似被平台截断:
      1) 以省略号结尾 且 字节>=byte_threshold(截断簇 438-445B)
      2) 或 >=140字 且 词中截断(结尾是汉字/数字/字母)
    """
    s = summary.strip()
    if not s:
        return False
    ends_ell = s.endswith("...") or s.endswith("…")
    if ends_ell and len(s.encode("utf-8")) >= byte_threshold:
        return True
    if len(s) >= 140 and re.search(r"[\u4e00-\u9fff0-9a-zA-Z]$", s):
        return True
    return False


def probe(cid: str, debug_dir: Path, raw_rows: list[dict] | None = None) -> None:
    """探测单个 id: 试候选 API + 抓 HTML, 打印结果供人工确认。"""
    print(f"=== 探测 id={cid} ===")
    # 数据里真实的 url(带 sld 签名链接令牌)
    real_url = ""
    if raw_rows:
        row = next((r for r in raw_rows if r["id"] == cid), None)
        real_url = (row or {}).get("url", "")
    print(f"  数据中的 url: {real_url or '(未找到)'}")
    for url in API_CANDIDATES:
        u = url.format(id=cid)
        try:
            body = fetch(u, timeout=10.0)
            head = body[:200].replace("\n", " ")
            kind = "JSON" if body.lstrip().startswith(("{", "[")) else "HTML/其他"
            print(f"  [API] {u}\n        -> {kind}: {head}")
            if kind == "JSON":
                try:
                    d = json.loads(body)
                    print(f"        JSON keys: {list(d.keys()) if isinstance(d, dict) else type(d)}")
                except Exception:
                    pass
        except Exception as e:
            print(f"  [API] {u}\n        -> 失败: {e}")
    for label, url in (("真实url(带sld)", real_url), ("无sld", BASE.format(cid))):
        if not url:
            continue
        try:
            html = fetch(url, timeout=15.0)
            debug_dir.mkdir(parents=True, exist_ok=True)
            fname = f"{cid}_{'with_sld' if 'sld' in url else 'no_sld'}.html"
            (debug_dir / fname).write_text(html, "utf-8")
            print(f"  [HTML:{label}] {url}\n        -> 已保存 {debug_dir / fname} ({len(html)}B)")
            full = extract_full_text(html)
            print(f"        提取结果({len(full)}字): {full[:120]}")
        except Exception as e:
            print(f"  [HTML:{label}] 失败: {e}")


def main() -> None:
    p = argparse.ArgumentParser(description="抓详情页补全被截断的投诉文本")
    p.add_argument("--input", default="data/raw/hemao_complaints.csv")
    p.add_argument("--output", default="data/raw/full_text_patch.csv")
    p.add_argument("--debug-dir", default="data/debug/detail_pages")
    p.add_argument("--fail-log", default="data/raw/fetch_failures.log")
    p.add_argument("--probe", default="", help="只探测指定 id 的接口/页面结构, 不批量抓取")
    p.add_argument("--all", action="store_true", help="抓全部行(默认只抓疑似截断)")
    p.add_argument("--limit", type=int, default=0, help="最多抓 N 条(0=不限)")
    p.add_argument("--delay", type=float, default=1.5, help="请求间隔秒")
    p.add_argument("--resume", action="store_true", help="跳过 patch 里已抓取成功的 id")
    p.add_argument("--debug-samples", type=int, default=0, help="保存前 N 个原始HTML到debug目录")
    args = p.parse_args()

    debug_dir = Path(args.debug_dir)
    in_path, out_path = Path(args.input), Path(args.output)
    rows = list(csv.DictReader(open(in_path, encoding="utf-8-sig")))

    if args.probe:
        probe(args.probe, debug_dir, rows)
        return

    if args.all:
        targets = rows
    else:
        targets = [r for r in rows if is_suspicious(r.get("summary", ""))]
    if args.limit:
        targets = targets[: args.limit]

    # resume: 跳过已抓成功的
    done_ids: set[str] = set()
    if args.resume and out_path.exists():
        done_ids = {r["id"] for r in csv.DictReader(open(out_path, encoding="utf-8-sig"))
                    if r["ok"] == "1"}
        targets = [r for r in targets if r["id"] not in done_ids]
    print(f"原始 {len(rows)} 行, 待抓取 {len(targets)} 行"
          + (f" (resume 跳过 {len(done_ids)})" if done_ids else ""))

    debug_dir.mkdir(parents=True, exist_ok=True)
    results, failures = [], []
    for i, r in enumerate(targets, 1):
        cid = r["id"]
        # 优先用数据里真实的 url(带 sld 签名链接令牌), 否则退回拼接
        page_url = (r.get("url") or "").strip() or BASE.format(cid)
        try:
            html = fetch(page_url, timeout=15.0)
            if args.debug_samples and i <= args.debug_samples:
                (debug_dir / f"{cid}.html").write_text(html, "utf-8")
            full = extract_full_text(html)
            ok = 1 if full else 0
            results.append({
                "id": cid, "full_text": full, "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "ok": ok, "summary_len": len(r.get("summary", "")), "full_len": len(full),
            })
            print(f"  [{i}/{len(targets)}] {cid} {'OK(' + str(len(full)) + '字)' if ok else '提取为空'}")
            if not ok:
                failures.append(cid)
        except Exception as e:  # noqa: BLE001
            results.append({"id": cid, "full_text": "", "fetched_at": "",
                            "ok": 0, "summary_len": len(r.get("summary", "")), "full_len": 0})
            failures.append(cid)
            print(f"  [{i}/{len(targets)}] {cid} 请求失败: {e}")
        time.sleep(args.delay)

    # 合并已有结果(resume 时)
    if args.resume and out_path.exists():
        old = list(csv.DictReader(open(out_path, encoding="utf-8-sig")))
        old_ids = {r["id"] for r in old}
        results = [r for r in old if r["id"] not in {x["id"] for x in results}] + results
        _ = old_ids
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "full_text", "fetched_at", "ok", "summary_len", "full_len"])
        w.writeheader()
        w.writerows(results)
    Path(args.fail_log).write_text(
        "\n".join(f"{cid}\t{time.strftime('%Y-%m-%d %H:%M:%S')}" for cid in failures) + "\n", "utf-8")

    n_ok = sum(1 for x in results if x["ok"])
    print(f"\n完成: 成功 {n_ok}/{len(results)} (累计)")
    print(f"补丁文件: {out_path}")
    print(f"失败日志: {args.fail_log} (失败行保持原 summary, 无数据丢失)")


if __name__ == "__main__":
    main()
