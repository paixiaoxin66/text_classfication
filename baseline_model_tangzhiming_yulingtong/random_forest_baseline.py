# -*- coding: utf-8 -*-
"""随机森林基线 —— 同一真实测试集, 与 NB/LR/SVM 相同 TF-IDF(char_wb) 特征空间
RF 对内存敏感, 用 chi2 选择 Top8000 特征(与其它模型同一 50000 维空间中选取)
"""
import csv
import time

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, classification_report


def load(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return [r["text"] for r in rows], [r["category"] for r in rows]


X_tr, y_tr = load("data/processed/train_augmented.csv")
X_te, y_te = load("data/processed/test_real.csv")
print(f"训练 {len(X_tr)} / 测试 {len(X_te)} / 类别 {len(set(y_tr))}", flush=True)

t0 = time.time()
vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), max_features=50000,
                      sublinear_tf=True, min_df=2)
X_tr = vec.fit_transform(X_tr)
X_te = vec.transform(X_te)
print(f"TF-IDF 维度 {X_tr.shape[1]}, 用时 {time.time()-t0:.1f}s", flush=True)

t0 = time.time()
sel = SelectKBest(chi2, k=8000)
X_tr_s = sel.fit_transform(X_tr, y_tr)
X_te_s = sel.transform(X_te)
print(f"chi2 选特征 -> {X_tr_s.shape[1]}, 用时 {time.time()-t0:.1f}s", flush=True)

t0 = time.time()
clf = RandomForestClassifier(n_estimators=200, max_features="sqrt",
                             n_jobs=1, random_state=42, verbose=0)
clf.fit(X_tr_s, y_tr)
print(f"RF 训练完成, 用时 {time.time()-t0:.1f}s", flush=True)

y_p = clf.predict(X_te_s)
acc = accuracy_score(y_te, y_p)
macro = f1_score(y_te, y_p, average="macro")
weighted = f1_score(y_te, y_p, average="weighted")
print(f"\n随机森林(char_wb+chi2-8000) 测试集: acc={acc:.4f} macroF1={macro:.4f} weightedF1={weighted:.4f}")
print(classification_report(y_te, y_p, digits=4))
