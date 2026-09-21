import torch
from _01_config import Config

config = Config()

class MyBertClassfier(torch.nn.Module):
    def __init__(self):
        super().__init__()
        # 隐藏层使用bert的原始结构
        self.bert = config.bert_model
        # bert输出768维度,自己额外添加线性层转换为class_num维
        self.out = torch.nn.Linear(config.bert_config.hidden_size, config.class_num)

    def forward(self, batch_x):
        # batch_x 是一个包含 input_ids, attention_mask, token_type_ids 的字典
        result = self.bert(**batch_x)
        # 768维 -> class_num维
        logits = self.out(result['pooler_output'])
        return logits

if __name__ == '__main__':
    # 注意：直接运行需要先安装并下载好 bert
    from _02_dataloader_utils import build_all_dataloader
    mybert = MyBertClassfier()
    train_dataloader, _, _ = build_all_dataloader()
    for batch_x, batch_y in train_dataloader:
        print(f"真实结果: {batch_y}")
        logits = mybert(batch_x)
        print(f"预测分数: {logits}")
        break