import torch
from _01_d_config import Config
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from tqdm import tqdm

config = Config()


def model_eval(dev_dataloader, my_bert_model, device=config.device):
    my_bert_model.eval()
    with torch.no_grad():
        all_pred_labels, all_true_labels = [], []
        for batch_x, batch_y in tqdm(dev_dataloader):
            # 字典必须用推导式转移到设备
            batch_x = {k: v.to(device) for k, v in batch_x.items()}
            logits_y = my_bert_model(batch_x)
            all_true_labels.extend(batch_y.tolist())
            batch_pred_labels = torch.argmax(logits_y, dim=-1)
            all_pred_labels.extend(batch_pred_labels.tolist())

        acc = accuracy_score(all_true_labels, all_pred_labels)
        pre = precision_score(all_true_labels, all_pred_labels, average='macro', zero_division=0)
        rec = recall_score(all_true_labels, all_pred_labels, average='macro', zero_division=0)
        f1 = f1_score(all_true_labels, all_pred_labels, average='macro', zero_division=0)
        return acc, pre, rec, f1