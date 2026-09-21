import os
import pickle
import jieba
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from _01_config import Config

config = Config()


def process_data(base_path, process_path, label_encoder=None, fit_label=False):
    df = pd.read_csv(base_path, encoding='utf-8-sig')
    df = df.dropna(subset=['category', 'ask']).drop_duplicates().reset_index(drop=True)

    df['category'] = df['category'].astype(str).str.strip()
    df['ask'] = df['ask'].astype(str).str.strip()

    # 分词
    df['words'] = df['ask'].apply(lambda x: " ".join(jieba.lcut(x)))

    if fit_label:
        # 用训练集生成类别编码
        label_encoder = LabelEncoder()
        df['label'] = label_encoder.fit_transform(df['category'])

        # 保存类别文件
        os.makedirs(os.path.dirname(config.class_path), exist_ok=True)
        with open(config.class_path, 'w', encoding='utf-8') as f:
            for c in label_encoder.classes_:
                f.write(str(c) + '\n')

        # 保存 label_encoder
        os.makedirs(os.path.dirname(config.label_encoder_path), exist_ok=True)
        with open(config.label_encoder_path, 'wb') as f:
            pickle.dump(label_encoder, f)
    else:
        # dev/test 只保留训练集中出现过的类别
        known_classes = set(label_encoder.classes_)
        df = df[df['category'].isin(known_classes)].copy()
        df['label'] = label_encoder.transform(df['category'])

    os.makedirs(os.path.dirname(process_path), exist_ok=True)
    df.to_csv(process_path, index=False, encoding='utf-8-sig')

    return label_encoder


if __name__ == '__main__':
    # 先处理训练集，生成 label_encoder
    le = process_data(
        config.train_path,
        config.process_train_path,
        label_encoder=None,
        fit_label=True
    )

    # 再处理验证集和测试集
    process_data(
        config.dev_path,
        config.process_dev_path,
        label_encoder=le,
        fit_label=False
    )

    process_data(
        config.test_path,
        config.process_test_path,
        label_encoder=le,
        fit_label=False
    )

    print('分词并保存完成')