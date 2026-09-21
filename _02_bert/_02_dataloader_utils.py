import os
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import LabelEncoder
from _01_config import Config

config = Config()

# 全局 label_encoder，用于训练后保存
label_encoder = LabelEncoder()


class MyDataset(Dataset):
    def __init__(self, df, tokenizer, max_len):
        self.texts = df['ask'].astype(str).tolist()
        self.labels = df['label'].tolist()
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, index):
        text = self.texts[index]
        label = self.labels[index]

        # BERT 分词
        encoding = self.tokenizer(
            text,
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        # 去掉 batch 维度 (BERT tokenizer 返回 shape 为 [1, max_len])
        item = {k: v.squeeze(0) for k, v in encoding.items()}
        return item, torch.tensor(label, dtype=torch.long)


def build_all_dataloader():
    # 读取 CSV
    train_df = pd.read_csv(config.train_path, encoding='utf-8-sig')
    dev_df = pd.read_csv(config.dev_path, encoding='utf-8-sig')
    test_df = pd.read_csv(config.test_path, encoding='utf-8-sig')

    # 清理空值
    train_df = train_df.dropna(subset=['category', 'ask']).reset_index(drop=True)
    dev_df = dev_df.dropna(subset=['category', 'ask']).reset_index(drop=True)
    test_df = test_df.dropna(subset=['category', 'ask']).reset_index(drop=True)

    # 对标签进行编码 (只 fit 训练集)
    train_df['label'] = label_encoder.fit_transform(train_df['category'])

    # 处理 dev 和 test 中可能出现的训练集没有的类别 (丢弃或者映射为未知，这里选择丢弃)
    known_classes = set(label_encoder.classes_)
    dev_df = dev_df[dev_df['category'].isin(known_classes)].copy()
    test_df = test_df[test_df['category'].isin(known_classes)].copy()

    dev_df['label'] = label_encoder.transform(dev_df['category'])
    test_df['label'] = label_encoder.transform(test_df['category'])

    # 保存 class.txt
    os.makedirs(os.path.dirname(config.class_path), exist_ok=True)
    with open(config.class_path, 'w', encoding='utf-8') as f:
        for c in label_encoder.classes_:
            f.write(str(c) + '\n')

    # 动态更新 config.class_num
    config.class_num = len(label_encoder.classes_)
    print(f"检测到 {config.class_num} 个类别，类别列表已保存到 class.txt")

    # 构建 Dataset
    train_dataset = MyDataset(train_df, config.bert_tokenizer, config.max_len)
    dev_dataset = MyDataset(dev_df, config.bert_tokenizer, config.max_len)
    test_dataset = MyDataset(test_df, config.bert_tokenizer, config.max_len)

    # 构建 DataLoader
    train_dataloader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=True)
    dev_dataloader = DataLoader(dev_dataset, batch_size=config.batch_size, shuffle=False)
    test_dataloader = DataLoader(test_dataset, batch_size=config.batch_size, shuffle=False)

    return train_dataloader, test_dataloader, dev_dataloader