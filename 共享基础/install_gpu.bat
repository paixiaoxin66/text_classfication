@echo off
REM ============================================================
REM GPU 设备一键准备 (Windows + NVIDIA 显卡)
REM 注意: GTX 10/16系列(Pascal)不支持CUDA12, 把第3步改成 cu118
REM ============================================================
echo === [1/4] install deps (uv sync) ===
uv sync
if errorlevel 1 goto :fail

echo === [2/4] GPU info ===
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
if errorlevel 1 echo (nvidia-smi 未找到, 请先装 NVIDIA 驱动)

echo === [3/4] install CUDA torch (RTX 20/30/40 series -> cu124) ===
uv pip install torch==2.6.0+cu124 --index-url https://download.pytorch.org/whl/cu124
if errorlevel 1 goto :fail

echo === [4/4] verify ===
REM 注意: 用 .venv\Scripts\python.exe 直接验证/训练, 不要用 uv run
REM (uv run 会按 uv.lock 把 cu124 torch 还原成 CPU 版)
.venv\Scripts\python.exe -c "import torch; print('torch', torch.__version__); print('cuda:', torch.cuda.is_available()); print('gpu:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none')"
if errorlevel 1 goto :fail

echo.
echo [OK] 准备完成, 开始训练(注意用 .venv\Scripts\python.exe, 不要用 uv run):
echo   .venv\Scripts\python.exe train_bert.py --epochs 3 --batch-size 32
pause
exit /b 0

:fail
echo [ERROR] 某一步失败, 请查看上方报错
pause
exit /b 1
