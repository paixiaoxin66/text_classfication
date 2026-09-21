from _01_p_config import Config
import torch
import csv

config = Config()


def load_data_list(base_path):
    """
    读取 csv 数据，返回 [(文本, 标签), ...]
    """
    data_list = []
    with open(base_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)  # 跳过表头 category,ask
        for row in reader:
            if len(row) < 2:
                continue
            category, ask = row[0].strip(), row[1].strip()
            if category not in config.class2id:
                print(f"[警告] 未知类别: {category}，已跳过")
                continue
            label = config.class2id[category]
            data_list.append((ask, label))
    return data_list


class MyDataSet(torch.utils.data.Dataset):
    def __init__(self, data_list):
        self.data_list = data_list

    def __len__(self):
        return len(self.data_list)

    def __getitem__(self, index):
        return self.data_list[index]


def my_collate_fn(batch_data):
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


def build_all_dataloader():
    train_data_list = load_data_list(config.train_path)
    train_dataloader = torch.utils.data.DataLoader(
        MyDataSet(train_data_list), config.batch_size,
        collate_fn=my_collate_fn, shuffle=True
    )
    test_data_list = load_data_list(config.test_path)
    test_dataloader = torch.utils.data.DataLoader(
        MyDataSet(test_data_list), config.batch_size,
        collate_fn=my_collate_fn, shuffle=False
    )
    dev_data_list = load_data_list(config.dev_path)
    dev_dataloader = torch.utils.data.DataLoader(
        MyDataSet(dev_data_list), config.batch_size,
        collate_fn=my_collate_fn, shuffle=False
    )
    return train_dataloader, test_dataloader, dev_dataloader


if __name__ == '__main__':
    train_dl, test_dl, dev_dl = build_all_dataloader()
    for batch_x, batch_y in train_dl:
        print("batch_x keys:", batch_x.keys())
        print("batch_y:", batch_y[:5])
        break