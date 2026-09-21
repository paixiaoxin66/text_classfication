import torch
from _01_config import Config
from _02_dataloader_utils import build_all_dataloader
from _03_bert_classifier_model import MyBertClassfier
from _04_bert_model_eval_utils import model_eval
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from tqdm import tqdm
import os

config = Config()


def model_train():
    # 准备数据
    train_dataloader, test_dataloader, dev_dataloader = build_all_dataloader()

    # 准备模型
    my_bert_model = MyBertClassfier()
    my_bert_model.train()
    my_bert_model.to(config.device)  # 模型移到 GPU

    # 准备损失函数和优化器
    loss_fn = torch.nn.CrossEntropyLoss(reduction='mean')
    optimizer = torch.optim.AdamW(my_bert_model.parameters(), lr=config.lr, betas=(0.9, 0.999))

    best_score = 0

    # 确保模型保存文件夹存在
    os.makedirs(os.path.dirname(config.bert_model_save_path), exist_ok=True)

    for epoch in range(1, config.epochs + 1):
        total_loss, cnt = 0, 0
        all_pred_labels, all_true_labels = [], []

        for index, (batch_x, batch_y) in tqdm(enumerate(train_dataloader, start=1)):
            # TODO 修复：batch_x 是字典，需要遍历字典移入设备
            batch_x = {k: v.to(config.device) for k, v in batch_x.items()}
            batch_y = batch_y.to(config.device)

            # 前向传播
            logits_y = my_bert_model(batch_x)
            loss = loss_fn(logits_y, batch_y)

            # 梯度清零、反向传播、参数更新
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            # 日志统计
            total_loss += loss.item()
            cnt += 1
            all_true_labels.extend(batch_y.tolist())
            batch_pred_labels = torch.argmax(logits_y, dim=-1)
            all_pred_labels.extend(batch_pred_labels.tolist())

            # 每 10 批打印一次训练日志
            if index % 10 == 0 or index == len(train_dataloader):
                loss = total_loss / cnt
                acc = accuracy_score(all_true_labels, all_pred_labels)
                pre = precision_score(all_true_labels, all_pred_labels, average='macro', zero_division=0)
                rec = recall_score(all_true_labels, all_pred_labels, average='macro', zero_division=0)
                f1 = f1_score(all_true_labels, all_pred_labels, average='macro', zero_division=0)
                print(
                    f"训练日志:轮次{epoch},批次:{index},损失:{loss:.4f},准确率:{acc:.4f},精确率:{pre:.4f},召回率:{rec:.4f},f1分数:{f1:.4f}")

                total_loss, cnt = 0, 0
                all_pred_labels, all_true_labels = [], []

            # 每 200 批评估一次
            if index % 200 == 0 or index == len(train_dataloader):
                current_acc, current_pre, current_rec, current_f1 = model_eval(dev_dataloader, my_bert_model)
                print(
                    f"评估日志:准确率:{current_acc:.4f},精确率:{current_pre:.4f},召回率:{current_rec:.4f},f1分数:{current_f1:.4f}")

                # 恢复训练模式
                my_bert_model.train()

                if current_f1 > best_score:
                    best_score = current_f1
                    torch.save(my_bert_model.state_dict(), config.bert_model_save_path)
                    print(f"当前最优f1分数:{best_score:.4f},模型已经覆盖保存")


if __name__ == '__main__':
    model_train()