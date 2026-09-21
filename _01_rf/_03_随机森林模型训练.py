import os
import time
import pickle
import pandas as pd
from _01_config import Config
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

config = Config()

# 1. 读取训练集分词后数据
df_train = pd.read_csv(config.process_train_path, encoding='utf-8-sig')
x_train = df_train['words'].astype(str)
y_train = df_train['label']

# 2. 停用词
if os.path.exists(config.stop_words_path):
    stop_words = [
        line.strip()
        for line in open(config.stop_words_path, 'r', encoding='utf-8')
        if line.strip()
    ]
else:
    stop_words = []

# 3. TF-IDF
tfidf = TfidfVectorizer(
    stop_words=stop_words,
    max_features=50000,
    ngram_range=(1, 2)
)
X_train = tfidf.fit_transform(x_train)

# 4. 随机森林训练
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    n_jobs=-1,
    verbose=1
)

start_time = time.time()
print('开始训练...')
model.fit(X_train, y_train)
print(f'训练结束，耗时：{time.time() - start_time:.2f} 秒')

# 5. 用 dev 集评估
df_dev = pd.read_csv(config.process_dev_path, encoding='utf-8-sig')
X_dev = tfidf.transform(df_dev['words'].astype(str))
y_dev = df_dev['label']
y_pred = model.predict(X_dev)

print('dev 准确率:', accuracy_score(y_dev, y_pred))
print('dev 精确率:', precision_score(y_dev, y_pred, average='macro', zero_division=0))
print('dev 召回率:', recall_score(y_dev, y_pred, average='macro', zero_division=0))
print('dev f1:', f1_score(y_dev, y_pred, average='macro', zero_division=0))

# 6. 保存 tfidf 和模型
os.makedirs(os.path.dirname(config.tfidf_save_path), exist_ok=True)
os.makedirs(os.path.dirname(config.rf_save_model_path), exist_ok=True)

with open(config.tfidf_save_path, 'wb') as f:
    pickle.dump(tfidf, f)

with open(config.rf_save_model_path, 'wb') as f:
    pickle.dump(model, f)

print('tfidf 和 rf 模型保存成功')