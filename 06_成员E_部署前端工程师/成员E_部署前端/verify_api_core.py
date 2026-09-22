# -*- coding: utf-8 -*-
"""模拟 api_server 的核心推理逻辑, 验证后端可用性"""
import os, json
os.environ["HF_HUB_OFFLINE"] = "1"
import torch
from transformers import BertForSequenceClassification, BertTokenizer

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE, "data", "out", "bert_model")
LABEL = os.path.join(BASE, "data", "out", "label_map.json")

label_map = json.load(open(LABEL, encoding="utf-8"))
inv = {v: k for k, v in label_map.items()}
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tok = BertTokenizer.from_pretrained(MODEL_DIR)
model = BertForSequenceClassification.from_pretrained(MODEL_DIR).to(device).eval()
print(f"模型加载 OK: {len(label_map)} 类, 设备={device}")

text = "我在网课熊平台购买执业药师课程被骗680元，要求退还课程费用并道歉"
enc = tok(text, max_length=128, padding="max_length", truncation=True, return_tensors="pt").to(device)
with torch.no_grad():
    probs = torch.softmax(model(**enc).logits, dim=-1)[0].cpu().tolist()
preds = [{"label": inv[i], "probability": round(p, 6)} for i, p in enumerate(probs)]
preds.sort(key=lambda x: x["probability"], reverse=True)
print("Top5:", [(p["label"], f"{p['probability']*100:.1f}%") for p in preds[:5]])
print("共返回类别数:", len(preds))
assert len(preds) == 18, "必须返回 18 类"
assert preds[0]["label"] == "教育", f"预期教育, 实际 {preds[0]['label']}"
print("后端核心逻辑验证通过 ✓")
