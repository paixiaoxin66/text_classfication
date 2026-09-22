# 黑猫投诉爬虫 (hemao-scraper)

「AI消费维权助手」项目的数据采集脚本。

黑猫投诉是**动态站点**（切换"最新投诉/最热投诉"时网址栏不变），真实数据来自带签名的 JSON 接口：
`https://tousu.sina.cn/api/index/feed?ts=&rs=&signature=&type=2&page_size=10&page=N`

本脚本直接调用该接口（签名算法来自开源项目 [yeyeye777/toususina](https://github.com/yeyeye777/toususina)，实测可行），
对应爬虫五步法：**找URL规律 → 发请求 → 提字段 → 存CSV → for循环翻页**。

## 环境要求

- 已安装 [uv](https://docs.astral.sh/uv/)（推荐）；或 pip + Python ≥ 3.10
- **必须在能联网的本机运行**

## 快速开始

```bash
cd hemao_scraper
uv sync                # 只需 requests 一个依赖
uv run python scraper.py --inspect        # 第1步：看接口返回哪些字段（务必先跑）
uv run python scraper.py --max-items 500  # 第2步：小批量验证
uv run python scraper.py --max-items 50000  # 第3步：正式爬（最新投诉，默认）
uv run python scraper.py --resume --max-items 50000  # 断点续爬
```

## 参数说明

| 参数 | 默认 | 说明 |
|---|---|---|
| `--types` | 2 | 要爬的接口 type 列表（逗号分隔）。type=2=最新投诉；其他值用 `--probe` 探测（实测 6~20 与 5 重复） |
| `--fields` | 空 | 🎯 按领域循环爬：逗号分隔 field 列表，如 `6,25,48`。**探测已确认有效**，每领域可翻 50 页(~500条)，18 领域可再拿 8~9 千条且类别更均衡 |
| `--page-size` | 10 | 每页条数（实测服务端固定~10条，调大无效） |
| `--max-items` | 30000 | 全局最大抓取条数 |
| `--max-pages` | 10000 | 单个 type 最多翻页数（保险丝；每个 feed 实际只有 50 页） |
| `--delay` | 1.5 | 每页请求间隔秒。⚠️ 实测风控阈值约 **40~50 次/分钟**，**建议 ≥2.0**（约20次/分钟最稳） |
| `--resume` | 关 | 断点续爬（记住每个 type 爬到的页数） |
| `--inspect` | 关 | 抓一页接口数据存 `data/debug/feed_sample.json` 并打印字段清单 |
| `--probe` | 关 | 探测哪些 type 有数据/能翻多深（探测本身 34 次请求，别频繁跑） |
| `--timeout` | 15 | 请求超时秒 |

## 数据字段

输出 `data/hemao_complaints.csv`（UTF-8-BOM，Excel 直接打开）：

| 字段 | 说明 |
|---|---|
| id | 投诉编号（来自详情URL） |
| category | 投诉领域/类别（接口 main 中有 industry/category 等字段时自动填入，否则为空） |
| title | 投诉标题 |
| timestamp / datetime | 时间戳 / 可读时间 |
| summary | 投诉内容摘要 |
| cotitle | 投诉对象（企业） |
| appeal | 投诉诉求（如退款、赔偿） |
| issue | 投诉问题类型（如退款问题、服务态度）——**可直接当分类标签用** |
| status | 处理状态（接口有则提取） |
| url | 详情页链接 |
| extra_json | 未识别的原始字段（JSON），不丢数据 |

> 💡 **关于分类标签**：本项目要做"投诉领域分类"。接口 `main` 里若有 `industry/category` 类字段会自动进 `category` 列；
> 若没有，`issue`（投诉问题）本身就是不错的多分类标签；需要更细的"行业"标签可后期爬详情页补充。
> **先 `--inspect` 看 `main 字段清单` 确认到底有哪些字段。**

## 断点续爬

- 进度存 `data/progress.json`（已抓 id + 已到第几页）；中断后 `--resume` 从上次页继续，自动去重；
- CSV 增量追加，每 50 条落盘一次。

## 速度参考

API 模式每页 10 条，`--delay 1` 时约 **3.6万条/小时**：

| 目标 | 耗时（--delay 1.0） |
|---|---|
| 3万条 | ~50 分钟 |
| 5万条 | ~1.5 小时 |
| 10万条 | ~3 小时 |

嫌慢就 `--delay 0.4`（约快一倍），但仍建议保持 ≥0.3 防封。

## 注意事项

- **先 `--inspect` + 小批量**：确认接口能通、字段齐全再全量；
- **电源设"从不睡眠"**；中断用 `--resume` 续爬即可；
- **被限流**：日志连续 403/429 → 停 2~4 小时或换网络 → `--resume`（降低 `--delay`）；
- **别挂代理/VPN**，直连最稳；
- **合规**：数据含个人信息，教学用途务必脱敏，不公开传播。

## 常见问题速查

| 现象 | 处理 |
|---|---|
| `uv 不是内部或外部命令` | 装完 uv 重开终端；或 `pip install uv` |
| `--inspect` 请求失败/空 | 确认本机联网；电脑时间不准会签名失败；`--type` 换值试探；看 `data/debug/feed_sample.json` |
| signature 无效/401 | 检查电脑时间是否准确（签名依赖毫秒时间戳） |
| CSV category 为空 | 接口无行业字段，用 `issue` 当标签，或后期补爬详情页 |
| 重复很多 | 去重靠 id；若换参数重跑建议先删旧 CSV |
| 电脑睡着了中断 | 电源设从不睡眠；`--resume` 续爬 |

## 爬多少条合适？

**推荐 5万条**（`--max-items 50000`），API 模式 1.5 小时就能爬完，量够且省时间。
想更充足 10万也行（约3小时），**15万没必要**——8~15 类文本多分类到 5万条已接近准确率上限，
更重要的是用 `issue`/`category` 保证**类别均衡**（可后续清洗时做分层采样）。

## Web 前端 + 分类 API（答辩演示）

```
数据流水线(hemao_scraper) → data/out/bert_model → api_server.py(FastAPI:8000)
                                                        ↑ POST /api/v1/classify
                                              frontend/ (React+Vite:5173)
```

- 后端启动：`uv sync` 后 `uv run uvicorn api_server:app --host 0.0.0.0 --port 8000`
- 前端启动：`cd frontend && npm install && npm run dev` → http://localhost:5173
- 前端说明、API 配置、JSON 契约详见 `frontend/README.md`
- 后端未就绪时可开演示模式：`frontend/.env.development` 里 `VITE_USE_MOCK=true`
- 模型可用性自检：`.venv\Scripts\python.exe scripts\verify_api_core.py`
