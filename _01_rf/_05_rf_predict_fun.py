import pickle
import jieba
from _01_config import Config

config = Config()

# 1. 加载 tfidf
with open(config.tfidf_save_path, 'rb') as f:
    tfidf = pickle.load(f)

# 2. 加载随机森林模型
with open(config.rf_save_model_path, 'rb') as f:
    model = pickle.load(f)

# 3. 加载类别编码器
with open(config.label_encoder_path, 'rb') as f:
    label_encoder = pickle.load(f)


def predict_fun(data):
    # 4.1 获取文本并分词
    text = data.get('text', '')
    words = " ".join(jieba.lcut(text))

    # 4.2 TF-IDF 转数值特征
    number_words = tfidf.transform([words])

    # 4.3 模型预测数字标签
    y_pred = model.predict(number_words)[0]

    # 4.4 数字标签还原成中文类别
    y_pred_class = label_encoder.inverse_transform([y_pred])[0]

    # 4.5 拼接到 data 中并返回
    data['predict_class'] = y_pred_class
    return data


if __name__ == '__main__':
    text = input('请输入一段文本：')
    data = {"text": text}
    result = predict_fun(data)
    print(result)