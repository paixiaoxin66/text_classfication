import pickle
import pandas as pd
from _01_config import Config
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from sklearn.metrics import confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

config = Config()

# 1. 读取测试集分词后数据
df_test = pd.read_csv(config.process_test_path, encoding='utf-8-sig')
x_test = df_test['words'].astype(str)
y_test = df_test['label']

# 2. 加载 tfidf
with open(config.tfidf_save_path, 'rb') as f:
    tfidf = pickle.load(f)

X_test = tfidf.transform(x_test)

# 3. 加载模型
with open(config.rf_save_model_path, 'rb') as f:
    model = pickle.load(f)

y_pred = model.predict(X_test)

# 4. 评估
print('准确率:', accuracy_score(y_test, y_pred))
print('精确率:', precision_score(y_test, y_pred, average='macro', zero_division=0))
print('召回率:', recall_score(y_test, y_pred, average='macro', zero_division=0))
print('f1分数:', f1_score(y_test, y_pred, average='macro', zero_division=0))

# 5. 加载 label_encoder，打印详细报告
with open(config.label_encoder_path, 'rb') as f:
    label_encoder = pickle.load(f)

print(classification_report(
    y_test,
    y_pred,
    target_names=label_encoder.classes_,
    zero_division=0
))

# 用混淆矩阵证明数据可信度
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d',
            xticklabels=label_encoder.classes_,
            yticklabels=label_encoder.classes_,
            cmap='Blues')
plt.xlabel('预测值')
plt.ylabel('真实值')
plt.title('混淆矩阵')
plt.savefig('confusion_matrix.png', dpi=300, bbox_inches='tight')
print("混淆矩阵已保存为 confusion_matrix.png")