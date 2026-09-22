# -*- coding: utf-8 -*-
"""计算 NB 在 char_wb 特征下的真实测试指标(统计页数据用)"""
import csv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score, classification_report
from sklearn.naive_bayes import MultinomialNB

def load(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return [r["text"] for r in rows], [r["category"] for r in rows]

X_tr, y_tr = load("data/processed/train_augmented.csv")
X_te, y_te = load("data/processed/test_real.csv")
vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), max_features=50000, sublinear_tf=True, min_df=2)
X_tr = vec.fit_transform(X_tr)
X_te = vec.transform(X_te)
m = MultinomialNB(alpha=1.0).fit(X_tr, y_tr)
y_p = m.predict(X_te)
print("NB(char_wb) 测试集: acc=%.4f macroF1=%.4f weightedF1=%.4f" % (
    accuracy_score(y_te, y_p), f1_score(y_te, y_p, average="macro"), f1_score(y_te, y_p, average="weighted")))
