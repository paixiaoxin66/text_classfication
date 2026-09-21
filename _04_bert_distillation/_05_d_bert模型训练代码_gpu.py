import torch
import torch.nn.functional as F
from _01_d_config import Config
from _02_dataloader_utils import build_all_dataloader
from _03_bert_classifier_model import MyBertClassfier
from _03_distill_bilstm_model import MyBiLSTM
from _04_bert_model_eval_utils import model_eval
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from tqdm import tqdm

config = Config()
print(f"当前运行的设备: {config.device}")


def model_train():
    train_dataloader, test_dataloader, dev_dataloader = build_all_dataloader()

    # 教师模型
    my_bert_model = MyBertClassfier()
    my_bert_model.load_state_dict(torch.load(config.bert_model_save_path))
    my_bert_model.eval()
    my_bert_model.to(config.device)

    # 学生模型
    bilstm = MyBiLSTM()
    bilstm.train()
    bilstm.to(config.device)

    loss_fn = torch.nn.CrossEntropyLoss(reduction='mean')
    optimizer = torch.optim.AdamW(bilstm.parameters(), lr=config.lstm_lr, betas=(0.9, 0.999))

    best_score = 0

    for epoch in range(1, config.epochs + 1):
        total_loss, cnt = 0, 0
        all_pred_labels, all_true_labels = [], []

        for index, (batch_x, batch_y) in tqdm(enumerate(train_dataloader, start=1),
                                              total=len(train_dataloader),
                                              desc=f"Epoch {epoch}"):
            # 数据移到设备
            batch_y = batch_y.to(config.device)
            batch_x = {k: v.to(config.device) for k, v in batch_x.items()}

            # 教师模型前向（不需要梯度）
            with torch.no_grad():
                logits_bert = my_bert_model(batch_x)

            # 学生模型前向
            logits_bilstm = bilstm(batch_x)

            # 硬标签损失：使用真实标签 batch_y
            hard_loss = loss_fn(logits_bilstm, batch_y)

            # 软标签损失
            bert_soft_labels = F.log_softmax(logits_bert / config.T, dim=-1)
            bilstm_soft_labels = F.log_softmax(logits_bilstm / config.T, dim=-1)
            soft_loss = F.kl_div(bilstm_soft_labels, bert_soft_labels,
                                 reduction='batchmean', log_target=True)

            # 总损失
            loss = config.alpha * (config.T * config.T) * soft_loss + (1 - config.alpha) * hard_loss

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            cnt += 1
            all_true_labels.extend(batch_y.tolist())
            batch_pred_labels = torch.argmax(logits_bilstm, dim=-1)
            all_pred_labels.extend(batch_pred_labels.tolist())

            if index % 10 == 0 or index == len(train_dataloader):
                avg_loss = total_loss / cnt
                acc = accuracy_score(all_true_labels, all_pred_labels)
                pre = precision_score(all_true_labels, all_pred_labels, average='macro', zero_division=0)
                rec = recall_score(all_true_labels, all_pred_labels, average='macro', zero_division=0)
                f1 = f1_score(all_true_labels, all_pred_labels, average='macro', zero_division=0)
                print(f"训练日志: 轮次{epoch}, 批次:{index}, 损失:{avg_loss:.4f}, "
                      f"准确率:{acc:.4f}, 精确率:{pre:.4f}, 召回率:{rec:.4f}, f1:{f1:.4f}")
                total_loss, cnt = 0, 0
                all_pred_labels, all_true_labels = [], []

            if index % 200 == 0 or index == len(train_dataloader):
                current_acc, current_pre, current_rec, current_f1 = model_eval(dev_dataloader, bilstm)
                print(f"评估日志: 准确率:{current_acc:.4f}, 精确率:{current_pre:.4f}, "
                      f"召回率:{current_rec:.4f}, f1:{current_f1:.4f}")
                bilstm.train()
                if current_f1 > best_score:
                    best_score = current_f1
                    torch.save(bilstm.state_dict(), config.bilstm_distillation_save_path)
                    print(f"当前最优f1: {best_score:.4f}，模型已保存")


if __name__ == '__main__':
    model_train()