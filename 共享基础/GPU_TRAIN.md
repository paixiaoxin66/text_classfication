# GPU 设备训练手册（放到有 NVIDIA 显卡的设备上）

## 一、版本选型（先跑 nvidia-smi 看显卡名 + 驱动）

| 你的显卡 | PyTorch | CUDA 后缀 | 驱动要求(Windows) |
|---|---|---|---|
| RTX 20/30/40 系（推荐） | 2.6.0 | **cu124** | ≥ 551.61 |
| RTX 20 系（老驱动） | 2.5.x | cu121 | ≥ 531.14 |
| GTX 10/16 系（Pascal） | 2.2.x | **cu118** | ≥ 452.39 |

> 注意：**不需要单独装 CUDA Toolkit** —— torch 的 cu124/cu118 wheel 自带 CUDA 运行时，只要驱动够新即可。
> GTX 10/16 系（Pascal）不支持 CUDA 12，必须用 cu118。

## 二、三步训练（以 RTX 3090 为例）

```bash
# 1. 解压 + 进目录
unzip ai_weiquan_gpu_full_*.zip     # Windows 用资源管理器解压
cd hemao_scraper

# 2. 准备环境（脚本内: uv sync → 装cu124 torch → 验证GPU）
bash install_gpu.sh                 # Linux
install_gpu.bat                     # Windows

# 3. 训练（自动: 检测CUDA + 本地模型, 全程离线; 默认 fp32 最稳）
#    ⚠️ 必须用 .venv 里的 python 直接跑, 不要用 uv run
#    (uv run 会按 uv.lock 把 cu124 torch 还原成 CPU 版)
.venv/bin/python train_bert.py --epochs 3 --batch-size 32        # Linux  (fp32, 推荐)
.venv\Scripts\python.exe train_bert.py --epochs 3 --batch-size 32   # Windows (fp32, 推荐)

# 可选提速: 加 --amp 用混合精度(fp16, 快2-3倍; 若遇NaN会自动回退fp32)
.venv/bin/python train_bert.py --epochs 3 --batch-size 32 --amp
```

预计耗时（30000条 × 3轮）：
- RTX 3090 / 4090：**5~10 分钟**
- RTX 3060 / 3070：**10~20 分钟**

## 三、产物

```
data/out/bert_model/        ← 微调后模型(部署/演示用)
data/out/bert_report.txt    ← 准确率 + macro-F1 + 逐类报告(答辩用)
data/out/bert_confusion.png ← 混淆矩阵
```

## 四、常见问题

- **torch.cuda.is_available() 显示 False**：多半是装了 CPU 版 torch。重跑第 2 步脚本即可。
- **报 CUDA 驱动版本错误**：驱动太老，看 nvidia-smi 的 Driver Version，按上表换 cu 后缀。
- **显存不足(OOM)**：`--batch-size 16`（默认 16，若 24G 卡可升 32）。
- **想跑更快**：`--batch-size 32` 配 3090；数据少时可 `--epochs 2`。
