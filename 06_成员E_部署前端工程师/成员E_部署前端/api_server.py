#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消费者投诉文本分类系统 - FastAPI 后端
========================================
加载微调后的 BERT 模型(data/out/bert_model), 提供分类 API。

启动:
    uv run uvicorn api_server:app --host 0.0.0.0 --port 8000

接口:
    POST /api/v1/classify   {"text": "投诉内容"}
    -> {"text": "...", "predictions": [{"label":"教育","probability":0.9947}, ...18项...],
        "model": "bert-base-chinese"}

    GET /health  -> {"status": "ok", "model_loaded": true}
"""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ["HF_HUB_OFFLINE"] = "1"  # 使用本地模型, 禁止联网

import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from transformers import BertForSequenceClassification, BertTokenizer

BASE = Path(__file__).resolve().parent
MODEL_DIR = BASE / "data" / "out" / "bert_model"
LABEL_MAP_FILE = BASE / "data" / "out" / "label_map.json"

app = FastAPI(title="消费者投诉文本分类系统 API", version="1.0.0")

# 开发/演示阶段放开跨域(前端 Vite 5173 等)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- 模型加载(懒加载) ----------------
_model = None
_tokenizer = None
_label_map: dict[str, int] = {}


def load_model():
    global _model, _tokenizer, _label_map
    if _model is not None:
        return
    if not (MODEL_DIR / "model.safetensors").exists():
        raise RuntimeError(f"未找到微调模型: {MODEL_DIR}. 请先运行 train_bert.py")
    if not LABEL_MAP_FILE.exists():
        raise RuntimeError(f"未找到类别映射: {LABEL_MAP_FILE}")
    _label_map = json.loads(LABEL_MAP_FILE.read_text("utf-8"))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _tokenizer = BertTokenizer.from_pretrained(str(MODEL_DIR))
    _model = BertForSequenceClassification.from_pretrained(str(MODEL_DIR)).to(device).eval()
    print(f"[api] 模型已加载: {len(_label_map)} 类, 设备={device}")


class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500, description="投诉文本")


class Prediction(BaseModel):
    label: str
    probability: float


class ClassifyResponse(BaseModel):
    text: str
    predictions: list[Prediction]
    model: str


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": _model is not None}


@app.post("/api/v1/classify", response_model=ClassifyResponse)
def classify(req: ClassifyRequest):
    text = " ".join(req.text.split())
    if len(text) < 10:
        raise HTTPException(status_code=422, detail="投诉内容过短, 请补充到 10 字以上")
    try:
        load_model()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    device = next(_model.parameters()).device
    inv = {v: k for k, v in _label_map.items()}
    enc = _tokenizer(text, max_length=128, padding="max_length",
                     truncation=True, return_tensors="pt").to(device)
    with torch.no_grad():
        logits = _model(**enc).logits
        probs = torch.softmax(logits, dim=-1)[0].cpu().tolist()

    predictions = [
        {"label": inv[i], "probability": round(p, 6)}
        for i, p in enumerate(probs)
    ]
    predictions.sort(key=lambda x: x["probability"], reverse=True)
    return ClassifyResponse(text=text, predictions=predictions, model="bert-base-chinese")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
