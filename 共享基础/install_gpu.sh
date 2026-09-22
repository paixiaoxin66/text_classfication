#!/usr/bin/env bash
# ============================================================
# GPU 设备一键准备 (Linux 云服务器 / Linux 本地显卡机)
# 用法: bash install_gpu.sh
# 注意: GTX 10/16系列(Pascal)不支持CUDA12, 把第3步改成 cu118
# ============================================================
set -e
echo "=== [1/4] 安装依赖 (uv sync) ==="
uv sync

echo "=== [2/4] 显卡信息 (看 Driver Version 决定 torch 版本) ==="
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader || echo "(未检测到 nvidia-smi)"

echo "=== [3/4] 安装 CUDA 版 torch (RTX 20/30/40系 → cu124) ==="
uv pip install torch==2.6.0+cu124 --index-url https://download.pytorch.org/whl/cu124

echo "=== [4/4] 验证 GPU 可用 ==="
# 注意: 用 .venv/bin/python 直接验证/训练, 不要用 uv run
# (uv run 会按 uv.lock 把 cu124 torch 还原成 CPU 版)
.venv/bin/python -c "import torch; print('torch', torch.__version__); print('cuda可用:', torch.cuda.is_available()); print('显卡:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else '无')"

echo ""
echo "✅ 准备完成, 开始训练(注意用 .venv/bin/python, 不要用 uv run):"
echo "   .venv/bin/python train_bert.py --epochs 3 --batch-size 32"
