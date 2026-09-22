#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
黑猫投诉 API 爬虫（tousu.sina.cn/api/index/feed）
============================================================
黑猫投诉是动态站点：真实数据来自带签名(signature)的 JSON 接口。
本脚本直接调用该接口（签名算法来自开源项目 yeyeye777/toususina）。

已知限制与对策
--------------
* 接口 type=2(最新投诉) 实际只放行约 50 页/500 条(声称 item_count 十万级是虚标)
* -> 用 --probe 探测哪些 type 有数据、能翻多深、page_size 能否调大
* -> 用 --types "1,2,3" 一次爬多个 feed, 去重合并, 数据量翻倍

用法
----
    uv sync
    uv run python scraper.py --probe                 # 1. 探测可用 type / 深度 / page_size
    uv run python scraper.py --types 2 --max-items 500   # 2. 小批量验证
    uv run python scraper.py --types "1,2,3" --max-items 50000  # 3. 多 feed 全量爬
    uv run python scraper.py --resume --types "1,2,3" --max-items 50000  # 断点续爬
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import random
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests

API_URL = "https://tousu.sina.cn/api/index/feed"
BASE_URL = "https://tousu.sina.com.cn/"
DETAIL_RE = re.compile(r"/complaint/view/(\d+)")

# 接口签名盐(来自开源项目, 公开值)
SIGN_SECRET = "$d6eb7ff91ee257475%"

# field 数字ID -> 投诉领域中文名
# 依据: 已抓样本按企业名交叉推断(如6=京东/阿里/拼多多->电商平台), 可自行修正/扩充;
# 未收录的ID保持数字原样, 不影响训练(标签数字/中文均可)
FIELD_MAP = {
    "0": "其他/未分类",
    "1": "共享出行",
    "6": "电商平台",
    "10": "数码3C",
    "16": "家居日用",
    "22": "服饰鞋包",
    "25": "物流快递",
    "28": "旅游出行",
    "37": "影音娱乐",
    "44": "教育",
    "48": "金融支付",
    "55": "通讯运营商",
    "60": "房产家装",
    "66": "本地生活",
    "71": "医疗健康",
    "75": "汽车",
    "82": "婚恋交友",
    "110": "母婴食品",
    "114": "游戏",
}

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]

CSV_COLUMNS = ["id", "category", "title", "timestamp", "datetime", "summary",
               "cotitle", "appeal", "issue", "status", "url", "extra_json"]

# main 中疑似"领域/类别"的字段名，命中则写入 category 列
CATEGORY_KEYS = ("industry", "category", "indus", "label", "field", "field_name")

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("hemao")


# ---------------- 第1步辅助: 构造接口签名 ----------------
def gen_rs_ts_signature(page: int, type_: int = 2, page_size: int = 10) -> tuple[str, str, str]:
    """构造接口鉴权三参数 ts/rs/signature（算法来自 yeyeye777/toususina）。"""
    chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    ts = str(int(time.time() * 1000))                          # 13位毫秒时间戳
    rs = "".join(random.choice(chars) for _ in range(16))      # 随机16位
    parts = [SIGN_SECRET, str(page_size), ts, str(type_), str(page), rs]
    parts.sort()                                               # 排序后拼接再sha256
    signature = hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()
    return ts, rs, signature


def build_feed_url(page: int, type_: int, page_size: int,
                   ts: str, rs: str, signature: str, field: int | None = None) -> str:
    url = (f"{API_URL}?ts={ts}&rs={rs}&signature={signature}"
           f"&type={type_}&page_size={page_size}&page={page}")
    if field is not None:
        url += f"&field={field}"
    return url


# ---------------- 第3步: 字段提取 ----------------
def parse_list_item(item: dict) -> dict | None:
    """把接口返回的单个投诉卡片转成一行 CSV 数据。"""
    main = item.get("main") or {}
    url = main.get("url") or ""
    if not url:
        return None
    full_url = urljoin(BASE_URL, url) if url.startswith("/") else url
    m = DETAIL_RE.search(full_url)
    cid = m.group(1) if m else str(main.get("id") or "")

    # 疑似领域字段 -> category 列(数字ID映射为中文领域名)
    category = ""
    for k in CATEGORY_KEYS:
        v = main.get(k)
        if v not in (None, ""):
            category = FIELD_MAP.get(str(v), str(v))
            break

    ts = main.get("timestamp")
    dt = ""
    if ts not in (None, ""):
        try:
            dt = datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            dt = str(ts)

    # 未识别的字段全部收进 extra_json, 不丢数据（领域字段已进 category, 不重复存）
    known = set(CSV_COLUMNS) | set(CATEGORY_KEYS) | {"extra_json"}
    extra = {k: v for k, v in main.items() if k not in known}

    return {
        "id": cid,
        "category": category,
        "title": main.get("title") or "",
        "timestamp": ts if ts is not None else "",
        "datetime": dt,
        "summary": main.get("summary") or "",
        "cotitle": main.get("cotitle") or "",
        "appeal": main.get("appeal") or "",
        "issue": main.get("issue") or "",
        "status": main.get("status") or "",
        "url": full_url,
        "extra_json": json.dumps(extra, ensure_ascii=False) if extra else "",
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="黑猫投诉 API 爬虫")
    p.add_argument("--output", default="data/hemao_complaints.csv", help="CSV 输出路径")
    p.add_argument("--progress", default="data/progress.json", help="断点进度文件")
    p.add_argument("--types", default="2",
                   help="要爬的接口type列表, 逗号分隔, 如 '2,3,4' (2=最新投诉; 其他值先用 --probe 探测)")
    p.add_argument("--field", type=int, default=None,
                   help="按领域过滤(如 6=电商平台), 需先用 --probe 探测D确认有效; 不签名, 有失效风险")
    p.add_argument("--fields", default="",
                   help="按领域循环爬: 逗号分隔的field列表, 如 '6,25,48' (探测D已确认有效; 留空=不按领域过滤)")
    p.add_argument("--page-size", type=int, default=10, help="每页条数(默认10, --probe 可测能否调大)")
    p.add_argument("--max-items", type=int, default=30000, help="全局最大抓取条数")
    p.add_argument("--max-pages", type=int, default=10000, help="单个type最多翻页数(保险丝)")
    p.add_argument("--delay", type=float, default=1.5,
                   help="每页请求间隔秒(默认1.5, 实测风控阈值约40-50次/分钟, 建议≥2.0)")
    p.add_argument("--stop-streak", type=int, default=5,
                   help="连续N页无新增则提前结束该type(实测types 6-20与5高度重叠, 省流量防风控)")
    p.add_argument("--resume", action="store_true", help="断点续爬")
    p.add_argument("--inspect", action="store_true",
                   help="抓一页接口数据存到 data/debug 并打印字段清单")
    p.add_argument("--probe", action="store_true",
                   help="探测: 哪些 type 有数据/能翻多深/page_size 能否调大")
    p.add_argument("--timeout", type=float, default=15.0)
    return p


class Scraper:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.seen: set[str] = set()
        self.last_pages: dict[str, int] = {}   # {type: 已爬到第几页}
        self.blocked = False                    # 是否被平台风控(456)
        self._empty_streak = 0                  # 连续无新增页数计数
        self.progress_path = Path(args.progress)
        self.out_path = Path(args.output)
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        self._csv_file = None
        self._csv_writer = None
        self._pending: list[dict] = []

    @staticmethod
    def _type_list(types_str: str) -> list[str]:
        return [t.strip() for t in str(types_str).split(",") if t.strip()]

    # ---------------- 第2步: 请求(带重试/限速) ----------------
    def get_json(self, url: str, retries: int = 3) -> dict | None:
        for attempt in range(1, retries + 1):
            try:
                r = requests.get(url, timeout=self.args.timeout, headers={
                    "User-Agent": random.choice(UA_LIST),
                    "Accept": "application/json, text/plain, */*",
                    "Referer": BASE_URL,
                    "Accept-Language": "zh-CN,zh;q=0.9",
                })
                if r.status_code == 200:
                    try:
                        return r.json()
                    except ValueError:
                        log.warning("返回非JSON(第%d次): %s 前80字符=%s",
                                    attempt, url, r.text[:80])
                elif r.status_code == 456:
                    # 平台风控: 立即停止, 不再重试(重试会加剧封禁)
                    log.warning("被平台风控 HTTP 456(请求过快被封). 停止爬取, 建议等 10~30 分钟后再 --resume")
                    self.blocked = True
                    return None
                elif r.status_code in (403, 429, 503):
                    log.warning("被限流 HTTP %s, 第%d次重试, 等待%ds",
                                r.status_code, attempt, attempt * 5)
                    time.sleep(attempt * 5)
                    continue
                else:
                    log.warning("HTTP %s: %s (等待 %ds 再重试)", r.status_code, url, attempt)
                    time.sleep(attempt)
            except requests.RequestException as e:
                log.warning("请求异常: %s (%s)", e, url)
                time.sleep(attempt * 2)
        return None

    def _sleep(self) -> None:
        time.sleep(self.args.delay * random.uniform(0.6, 1.6))

    # ---------------- 进度/CSV ----------------
    def load_progress(self) -> None:
        if self.args.resume and self.progress_path.exists():
            d = json.loads(self.progress_path.read_text("utf-8"))
            self.seen = set(d.get("seen", []))
            lp = d.get("last_pages")
            if isinstance(lp, dict):
                self.last_pages = {str(k): int(v) for k, v in lp.items()}
            elif d.get("last_page") is not None:   # 旧格式兼容
                first = self._type_list(self.args.types)[0]
                self.last_pages = {first: int(d["last_page"])}
            log.info("恢复进度: 已抓去重 %d 条, 各type页数 %s", len(self.seen), self.last_pages)

    def save_progress(self) -> None:
        d = {"seen": sorted(self.seen), "last_pages": self.last_pages,
             "updated": time.strftime("%Y-%m-%d %H:%M:%S")}
        self.progress_path.write_text(json.dumps(d, ensure_ascii=False, indent=2), "utf-8")

    def open_csv(self) -> None:
        # 文件已存在且未用 --resume 时, 备份旧文件再新建, 保证表头与数据 schema 一致
        if self.out_path.exists():
            if self.args.resume:
                self._csv_file = open(self.out_path, "a", newline="", encoding="utf-8-sig")
                self._csv_writer = csv.DictWriter(self._csv_file, fieldnames=CSV_COLUMNS)
                return
            bak = self.out_path.with_suffix(
                f".bak{time.strftime('%Y%m%d_%H%M%S')}{self.out_path.suffix}")
            log.warning("输出文件已存在且未使用 --resume, 备份为 %s 后新建", bak.name)
            self.out_path.replace(bak)
        self._csv_file = open(self.out_path, "a", newline="", encoding="utf-8-sig")
        self._csv_writer = csv.DictWriter(self._csv_file, fieldnames=CSV_COLUMNS)
        self._csv_writer.writeheader()

    def flush_rows(self) -> None:
        if not self._pending:
            return
        self._csv_writer.writerows(self._pending)
        self._csv_file.flush()
        self._pending = []

    def close_csv(self) -> None:
        if self._csv_file:
            self.flush_rows()
            self._csv_file.close()

    # ---------------- 第4/5步: 翻页抓取(支持多 type × 多 field) ----------------
    @staticmethod
    def _field_list(fields_str: str | None) -> list[str | None]:
        if not fields_str:
            return [None]
        return [f.strip() for f in str(fields_str).split(",") if f.strip()]

    def crawl(self) -> None:
        for t in self._type_list(self.args.types):
            if self.blocked:
                break
            for f in self._field_list(self.args.fields):
                if self.blocked:
                    break
                if self.args.max_items > 0 and len(self.seen) >= self.args.max_items:
                    break
                self._crawl_feed(t, f)

    def _feed_key(self, t: str, f: str | None) -> str:
        return f"{t}@{f}" if f else t

    def _crawl_feed(self, t: str, f: str | None) -> None:
        type_ = int(t)
        field = int(f) if f is not None else None
        key = self._feed_key(t, f)
        done = self.last_pages.get(key, 0)
        start = (done + 1) if self.args.resume else 1
        self._empty_streak = 0
        label = f"type={t}" + (f" field={f}" if field is not None else "")
        log.info("开始爬 %s, 从第 %d 页起(上次到第 %d 页)", label, start, done)
        for page in range(start, self.args.max_pages + 1):
            if self.args.max_items > 0 and len(self.seen) >= self.args.max_items:
                log.info("已达最大条数 %d, 停止", self.args.max_items)
                return
            ts, rs, sig = gen_rs_ts_signature(page, type_, self.args.page_size)
            url = build_feed_url(page, type_, self.args.page_size, ts, rs, sig, field=field)
            data = self.get_json(url)
            self._sleep()
            if data is None:
                if self.blocked:
                    log.warning("检测到平台风控, 本次运行停止; 请等待 10~30 分钟后再 --resume 续爬")
                    return
                log.warning("%s 第 %d 页获取失败, 本feed停止(可 --resume 续爬)", label, page)
                return
            lists = (data.get("result") or {}).get("data") or {}
            lists = lists.get("lists") or []
            if not lists:
                log.info("%s 第 %d 页无数据, 本feed到头", label, page)
                return
            new_rows = []
            for item in lists:
                row = parse_list_item(item)
                if not row or not row["id"]:
                    continue
                if row["id"] in self.seen:
                    continue
                self.seen.add(row["id"])
                new_rows.append(row)
            self._pending.extend(new_rows)
            if len(self._pending) >= 50:
                self.flush_rows()
                self.save_progress()
            self.last_pages[key] = page
            log.info("%s 第 %d 页: 接口返回 %d 条, 新增 %d 条, 累计 %d",
                     label, page, len(lists), len(new_rows), len(self.seen))
            # 连续 N 页无新增 -> 该feed与已抓数据高度重叠, 提前结束
            if len(new_rows) == 0:
                self._empty_streak += 1
                if self._empty_streak >= self.args.stop_streak:
                    log.info("%s 连续 %d 页无新增, 提前结束(数据重叠)", label, self.args.stop_streak)
                    return
            else:
                self._empty_streak = 0

    def run(self) -> None:
        self.load_progress()
        self.open_csv()
        try:
            self.crawl()
        except KeyboardInterrupt:
            log.warning("收到中断, 正在保存进度...")
        finally:
            self.close_csv()
            self.save_progress()
            log.info("完成: 共 %d 条唯一记录, 各type页数 %s", len(self.seen), self.last_pages)
            log.info("数据文件: %s", self.out_path.resolve())

    # ---------------- 调试: 看接口字段 ----------------
    def inspect(self) -> None:
        t = self._type_list(self.args.types)[0]
        ts, rs, sig = gen_rs_ts_signature(1, int(t), self.args.page_size)
        url = build_feed_url(1, int(t), self.args.page_size, ts, rs, sig,
                             field=self.args.field)
        data = self.get_json(url)
        if not data:
            log.error("接口请求失败: %s", url)
            return
        debug_dir = Path("data/debug")
        debug_dir.mkdir(parents=True, exist_ok=True)
        (debug_dir / "feed_sample.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
        log.info("已保存接口样例 -> data/debug/feed_sample.json")
        lists = (data.get("result") or {}).get("data") or {}
        lists = lists.get("lists") or []
        log.info("本页接口返回 %d 条投诉", len(lists))
        if lists:
            main = lists[0].get("main") or {}
            log.info("main 字段清单: %s", list(main.keys()))
            log.info("样例 title=%s | cotitle=%s | issue=%s | field=%s",
                     str(main.get("title"))[:40], str(main.get("cotitle"))[:20],
                     str(main.get("issue"))[:20], str(main.get("field"))[:20])
            log.info("main['field'] = 投诉领域(行业)标签, 已自动进 category 列")

    # ---------------- 探测: 找可用 type / 深度 / page_size ----------------
    def probe(self) -> None:
        log.info("=== 探测A: type=1..20 在第1页的数据量 ===")
        valid: list[int] = []
        for t in range(1, 21):
            ts, rs, sig = gen_rs_ts_signature(1, t, self.args.page_size)
            url = build_feed_url(1, t, self.args.page_size, ts, rs, sig)
            data = self.get_json(url)
            self._sleep()
            if not data:
                log.info("type=%-3d 请求失败/被拒", t)
                continue
            r = (data.get("result") or {}).get("data") or {}
            n = len(r.get("lists") or [])
            pg = r.get("pager") or {}
            log.info("type=%-3d 第1页 %d 条 | 声称page_amount=%s item_count=%s",
                     t, n, pg.get("page_amount"), pg.get("item_count"))
            if n > 0:
                valid.append(t)
        if not valid:
            log.warning("所有 type 均无数据, 检查网络/电脑时间/接口是否变化")
            return
        t0 = valid[0]
        log.info("=== 探测B: type=%d 的翻页深度(看第几页开始变空) ===", t0)
        for page in [1, 2, 10, 50, 51, 60, 100, 200, 500, 1000]:
            ts, rs, sig = gen_rs_ts_signature(page, t0, self.args.page_size)
            url = build_feed_url(page, t0, self.args.page_size, ts, rs, sig)
            data = self.get_json(url)
            self._sleep()
            n = 0
            if data:
                r = (data.get("result") or {}).get("data") or {}
                n = len(r.get("lists") or [])
            log.info("type=%d 第 %-5d 页: %d 条", t0, page, n)
        log.info("=== 探测C: page_size 是否可调大 (type=%d, 第1页) ===", t0)
        for ps in [10, 20, 50, 100]:
            ts, rs, sig = gen_rs_ts_signature(1, t0, ps)
            url = build_feed_url(1, t0, ps, ts, rs, sig)
            data = self.get_json(url)
            self._sleep()
            n = 0
            if data:
                r = (data.get("result") or {}).get("data") or {}
                n = len(r.get("lists") or [])
            log.info("page_size=%-4d -> 第1页 %d 条", ps, n)
        log.info("=== 探测D: field 参数是否有效 (type=2) ===")
        for f in [6, 25, 48]:
            for page in [1, 50]:
                ts, rs, sig = gen_rs_ts_signature(page, 2, self.args.page_size)
                url = build_feed_url(page, 2, self.args.page_size, ts, rs, sig, field=f)
                data = self.get_json(url)
                self._sleep()
                n, fields = 0, set()
                if data:
                    r = (data.get("result") or {}).get("data") or {}
                    lists = r.get("lists") or []
                    n = len(lists)
                    for it in lists:
                        m = it.get("main") or {}
                        if m.get("field") is not None:
                            fields.add(str(m["field"]))
                log.info("field=%-3d 第 %-3d 页: %d 条 | 实际field值=%s",
                         f, page, n, sorted(fields) if fields else "-")
        log.info("探测完成: 有效type=%s, 推荐运行: --types %s",
                 valid, ",".join(map(str, valid)))


def main() -> None:
    args = build_parser().parse_args()
    scraper = Scraper(args)
    if args.inspect:
        scraper.inspect()
        return
    if args.probe:
        scraper.probe()
        return
    scraper.run()


if __name__ == "__main__":
    main()
