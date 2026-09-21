# 导包
import torch

from _01_q_config import Config
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from tqdm import tqdm
# 创建对象
config = Config()


# 定义评估函数
def model_eval(dev_dataloader, my_bert_model,device=config.device):
    """
    :param dev_dataloader: 验证集数据
    :param my_bert_model: 当前训练的模型
    :return: acc,pre,rec,f1
    """
    # 设置模型为评估模式
    my_bert_model.eval()
    # 设置关闭梯度跟踪
    with torch.no_grad():
        # 额外添加评估指标相关的变量
        all_pred_labels, all_true_labels = [], []
        # 遍历dataloader拿到一批批数据预测
        for index, (batch_x, batch_y) in tqdm(enumerate(dev_dataloader, start=1)):
            # todo 放到设备上
            batch_x.to(device)
            # batch_x = {k: v.to(config.device) for k, v in batch_x.items()}
            # 前向传播
            logits_y = my_bert_model(batch_x)
            # 累加真实标签和预测的标签
            all_true_labels.extend(batch_y.tolist())
            batch_pred_labels = torch.argmax(logits_y, dim=-1)
            all_pred_labels.extend(batch_pred_labels.tolist())
        # todo 所有批次数据跑完后,计算评估指标
        acc = accuracy_score(all_true_labels, all_pred_labels)
        pre = precision_score(all_true_labels, all_pred_labels, average='macro')
        rec = recall_score(all_true_labels, all_pred_labels, average='macro')
        f1 = f1_score(all_true_labels, all_pred_labels, average='macro')
        # todo 返回结果,方便比较和打印日志
        return acc, pre, rec, f1
