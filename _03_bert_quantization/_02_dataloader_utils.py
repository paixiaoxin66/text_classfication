# 导包
from _01_q_config import Config
import torch
import csv

# 创建config对象
config = Config()


# todo 加载原始数据（适配 CSV 格式）
def load_data_list(base_path):
    """
    :param base_path: 数据的原始路径（CSV文件）
    :return: 列表格式: [(文本, 标签), (文本, 标签), ...]
    """
    data_list = []
    # 使用 utf-8-sig 去除 BOM 头
    with open(base_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)  # 跳过表头 category,ask
        for row in reader:
            if len(row) < 2:
                continue
            category, ask = row[0].strip(), row[1].strip()
            if category not in config.class2id:
                continue  # 跳过未知类别
            label = config.class2id[category]
            data_list.append((ask, label))
    return data_list


# todo 自定义dataset: 1个继承3个重写
class MyDataSet(torch.utils.data.Dataset):
    def __init__(self, data_list):
        self.data_list = data_list

    def __len__(self):
        return len(self.data_list)

    def __getitem__(self, index):
        return self.data_list[index]


# todo 自定义collate_fn函数
def my_collate_fn(batch_data):
    """
    :param batch_data: 一批 [(文本1,标签1),(文本2,标签2),...]
    :return: (文本张量字典, 标签张量)
    """
    texts, labels = zip(*batch_data)
    batch_labels_pt = torch.tensor(labels)
    batch_texts_pt = config.bert_tokenizer(
        texts,
        max_length=config.max_len,
        padding='max_length',
        truncation=True,
        return_tensors='pt'
    )
    return batch_texts_pt, batch_labels_pt


# todo 封装训练、测试、验证数据集对应的 dataloader
def build_all_dataloader():
    # 训练集
    train_data_list = load_data_list(config.train_path)
    train_dataset = MyDataSet(train_data_list)
    train_dataloader = torch.utils.data.DataLoader(
        train_dataset, config.batch_size, collate_fn=my_collate_fn, shuffle=True
    )
    # 测试集
    test_data_list = load_data_list(config.test_path)
    test_dataset = MyDataSet(test_data_list)
    test_dataloader = torch.utils.data.DataLoader(
        test_dataset, config.batch_size, collate_fn=my_collate_fn, shuffle=False
    )
    # 验证集
    dev_data_list = load_data_list(config.dev_path)
    dev_dataset = MyDataSet(dev_data_list)
    dev_dataloader = torch.utils.data.DataLoader(
        dev_dataset, config.batch_size, collate_fn=my_collate_fn, shuffle=False
    )
    return train_dataloader, test_dataloader, dev_dataloader


if __name__ == '__main__':
    train_dataloader, test_dataloader, dev_dataloader = build_all_dataloader()
    for batch_x, batch_y in train_dataloader:
        print(batch_x)
        print(batch_y)
        break