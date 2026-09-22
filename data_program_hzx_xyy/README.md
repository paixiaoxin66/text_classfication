# 数据流水线（数据清洗 → 划分 → 增强 → 过滤 → 最终数据集）

构建「AI消费维权助手」最终训练数据集（约 30000 条目标，质量优先）。

## 一键运行（推荐）

```bash
cd hemao_scraper
python scripts/build_dataset.py --target-size 30000 --seed 42
```

- 无 LLM 配置时自动走**规则增强**（纯标准库，本机可跑）；
- 配置了 LLM 时自动走 **LLM 语义改写**（`--mode llm` 强制指定，质量与多样性更高，可达 30000 条）；
- `--resume` 断点续跑；`--limit-originals N` 小规模测试；`--max-workers N` 控制 LLM 并发。

## 五个脚本（按顺序）

| 脚本 | 作用 | 输出 |
|---|---|---|
| `clean_complaints.py` | 15 项数据体检 + 清洗 + 去重 + 标签映射 | `data/processed/cleaned_complaints.csv`、`data/reports/data_quality_report.md`、`category_mapping.csv`、`category_distribution.csv`、`duplicate_report.csv` |
| `split_dataset.py` | 按类别分层 80/10/10 划分（seed 42） | `train_real.csv` / `val_real.csv` / `test_real.csv`、`split_distribution.csv` |
| `augment_dataset.py` | **只增强 Train**，类别均衡预算，LLM/规则双模式，断点续跑 | `data/augmentation/generated_raw.csv`、`failures.jsonl` |
| `filter_augmented.py` | 质量过滤（近重复/模板泛滥/金额完整性/LLM 元话术） | `generated_filtered.csv`、`augmentation_filter_stats.csv` |
| `build_dataset.py` | 统一入口：串联以上 + 泄漏检查 + 汇总报告 | `train_augmented.csv`（最终）、`augmentation_report.md` |

## 增强方法

**规则增强**（无 LLM 时，语义保持）：
- 领域同义词替换（退款→退钱/退回款项…，每次 2-4 处）
- 逗号分隔诉求列表重排（完整子句交换）
- 程度/持续性副词插入（不予退款→一直不予退款）
- 句间顺序交换

**LLM 语义改写**（配置时优先）：
- 13 条改写规则提示词，temperature 0.8，逐条改写
- 批量 + 重试(3次) + 退避 + 限速 + 断点续跑 + 失败日志

## 数字完整性三层防护

1. **数字保护**：增强前把金额/日期/数量替换为占位符，操作后还原；
2. **数字集合校验**：每个变体恢复后校验数字序列与原文完全一致，任何损伤即丢弃；
3. **过滤器兜底**：金额集合不一致的变体直接过滤。

## LLM 配置（可选）

在项目根目录 `.env` 或环境变量中配置（**绝不硬编码**，`.env` 已在 .gitignore）：

```
LLM_BASE_URL=https://api.xxx.com/v1/chat/completions
LLM_API_KEY=sk-xxxx
LLM_MODEL=your-model
```

## 输出文件说明

```
data/raw/hemao_complaints.csv           # 黑猫投诉原始数据(9043条, 永不修改)
data/processed/cleaned_complaints.csv   # 清洗后(8942条, 含325条'其他/未分类')
data/processed/train_real.csv           # Train 真实样本(6886条)
data/processed/val_real.csv             # Val 真实样本(854条, 100%真实)
data/processed/test_real.csv            # Test 真实样本(877条, 100%真实)
data/processed/train_augmented.csv      # 最终训练集(真实+增强, is_aug=0/1, 精简字段)
data/processed/train_augmented_full.csv # 最终训练集完整版(含全部原始字段: title/summary/cotitle/appeal/issue/status/datetime/url)
data/augmentation/generated_raw.csv     # 增强原始输出
data/augmentation/generated_filtered.csv# 通过质量检测的增强样本
data/reports/augmentation_report.md     # 最终报告(7节)
```

## 模型训练(数据流水线之后)

训练脚本已默认指向本流水线产物, 直接运行即可:

```bash
uv sync                       # 安装 scikit-learn/torch/transformers 等
uv run python train_baseline.py              # 基线: TF-IDF + NB/LR (约几分钟)
uv run python train_bert.py --epochs 3       # BERT 微调 (CPU 2~4小时, GPU 10~20分钟)
```

默认数据源:
- `--train` = `data/processed/train_augmented.csv`（30000 = 6886 真实 + 23114 增强）
- `--val` = `data/processed/val_real.csv`（854 条, 100% 真实）
- `--test` = `data/processed/test_real.csv`（877 条, 100% 真实）

模型产物输出到 `data/out/`（已在 .gitignore）。

## 已知问题: feed 接口 summary 截断与补全流程

**现象**: 黑猫 feed 接口的 `summary` 字段被平台按字节预算截断（UTF-8 约 445B ≈ 150 字）
**并补省略号 "..."**。实测 9043 条中 **4206 条（46.5%）**被截断（以省略号结尾且字节聚在 438-445B，
或词中截断），其中 **4003 条在 Train/Val/Test**。流水线本身不截断（已核对 text 与原始 title+summary 一致）。
完整正文只在详情页 `https://tousu.sina.cn/complaint/view/{id}/` 上。

**补全流程（需在能联网的本机执行）**:
```bash
# 0) 探测单个 id 的接口/页面结构(确认提取策略, 输出 HTML 样例)
uv run python scripts/fetch_full_text.py --probe 17399929650
# 1) 试跑 5 条, 核对提取效果
uv run python scripts/fetch_full_text.py --limit 5 --debug-samples 5 --delay 1.5
# 2) 全量抓疑似截断行(约4200条, delay 1.5 约 1.7~2 小时; 中断后 --resume 续跑)
uv run python scripts/fetch_full_text.py --delay 1.5
# 3) 回填生成 patched 原始数据(原文件不动)
python scripts/apply_full_text.py
# 4) 用补全后的数据重建全流程(确定性, seed 42, 结果可复现)
python scripts/build_dataset.py --target-size 30000 --seed 42 --raw data/raw/hemao_complaints_full.csv
```

**关键发现（已实测验证）**:
- 详情页必须带数据 `url` 字段里的 **`sld` 参数**（签名链接令牌），不带会返回"页面不存在"（4039B 无效页）
- 正文容器: `<div class="m-complaint-des4"><p>…完整正文…</p></div>`（实测瑞熊案例提取 401 字完整全文）
- 脚本已内置该提取模式 + "页面不存在"无效页防护；sld 可能过期，失败行自动保留原 summary

提取策略见 `fetch_full_text.py` 的 `EXTRACT_PATTERNS`；若页面结构变化导致提取为空，
用 `data/debug/detail_pages/` 下的 HTML 样例调整正则。失败行保持原 summary，不丢数据。

## 设计决策（答辩要点）

1. **只增强 Train**：Val/Test 100% 真实数据，杜绝评估泄漏；
2. **类别均衡预算**：A(<200 严重少数)最多增强 → B → C(400-700 轻量) → D(>700 最少)；
3. **质量优先于数量**：增强变体必须与原文本相似度 ≤ 0.93（3-5 处以上改写），
   与已通过样本 3-gram 相似度 ≤ 0.80（防模板泛滥），实际过滤率约 74%；
4. **可复现**：全局 seed 42 + 每样本确定性哈希派生 RNG，同命令多次运行结果一致；
5. **'其他/未分类'剔除**：混合行业噪声（教育/租车/餐饮/影城/软件），不入分类集，
   处理原因记录在 `category_mapping.csv`；
6. **规则模式诚实的上限**：短文本规则改写多样性有限，规则模式最终约 2.1 万条；
   要逼近 30000 请用 LLM 模式（`--mode llm`）。
