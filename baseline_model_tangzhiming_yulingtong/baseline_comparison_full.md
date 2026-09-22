# 模型基线完整对比报告

> 全部为**同一真实测试集**（877 条，100% 真实数据，seed=42 划分）上的结果
> 训练集：30,000 条（6,893 真实 + 23,107 增强，18 类）
> 传统模型特征：char_wb 字符级 n-gram(2-4) TF-IDF（max_features=50,000）

## 一、最终对比表

| 模型 | 准确率 | macro-F1 | weighted-F1 | 特点 |
|---|---|---|---|---|
| 朴素贝叶斯 | 72.41% | 68.26% | 72.30% | 概率基线（生成式假设强） |
| **FastText** | **71.95%** | **67.59%** | **71.94%** | 子词n-gram+平均嵌入，**训练69s/推理877条0.3s**，最快 |
| 随机森林 | 76.40% | 72.44% | 76.10% | chi2选8000特征+200棵树，训练32min |
| 逻辑回归 | 78.56% | 74.76% | 78.34% | 判别式基线 |
| 线性SVM | 79.70% | 75.87% | 79.41% | **最强传统基线** |
| **BERT 微调** | **85.40%** | **84.43%** | **85.33%** | bert-base-chinese，**主模型** |

**排名：BERT > 线性SVM > 逻辑回归 > 随机森林 > 朴素贝叶斯 > FastText**

## 二、关键结论（答辩要点）

1. **深度学习碾压传统方法**：BERT 比最强传统基线（线性SVM）高 **+5.70 准确率 / +8.56 macro-F1**——预训练语言模型对中文投诉文本语义理解的优势。
2. **判别式 > 生成式 > 词袋朴素**：SVM/LR 优于 NB（NB 的特征独立性假设对投诉文本不成立）。
3. **随机森林不敌线性模型**：高维稀疏文本特征下，线性模型（SVM/LR）比树模型（RF 76.4%）更适合——树模型在高维稀疏空间容易过拟合。
4. **FastText 的取舍**：精度最低但**速度碾压**（训练 69s vs BERT 数小时；推理 0.3s/877条 vs BERT ~数秒）——适合对延迟敏感、精度要求不高的场景。
5. **数据增强的红利**：增强主要提升弱模型（LR 增后 ≈ SVM 未增），对强模型中性（SVM M≈R）——见消融实验报告。

## 三、实现与复现

| 模型 | 脚本 | 输出 |
|---|---|---|
| 朴素贝叶斯/逻辑回归/线性SVM | `train_baseline_ablation.py` | `data/out/baseline_report.txt` |
| 随机森林 | `scripts/random_forest_baseline.py` | 见本报告 |
| FastText | `scripts/fasttext_baseline.py`（需 `.venv311`，Python 3.11 + fasttext-wheel）| `data/out/fasttext_model.bin` |
| BERT | `train_bert.py` | `data/out/bert_model/` |

> FastText 环境说明：官方 fasttext 无 Python 3.13 Windows wheel 且源码编译需 MSVC；
> 使用 `uv venv --python 3.11 .venv311` + `fasttext-wheel`（预编译）+ numpy 1.26（兼容修复）。
