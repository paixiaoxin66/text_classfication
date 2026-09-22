# 导包
from _01_q_config import Config
from _02_dataloader_utils import build_all_dataloader
import torch

# 创建对象
config = Config()


# todo 自定义bert分类模型: 1个继承2个重写
class MyBertClassfier(torch.nn.Module):
    def __init__(self):
        super().__init__()
        # 隐藏层使用bert的原始结构
        self.bert = config.bert_model
        # bert输出768维度不符合10分类结果要求,自己额外添加线性层转换
        self.out = torch.nn.Linear(config.bert_config.hidden_size, config.class_num)

    def forward(self, batch_x):
        # todo 利用预训练好的bert模型前向传播
        result = self.bert(**batch_x)
        # print(result['pooler_output'])  # result['last_hidden_state'][:,0,:]
        # todo 768维->10维
        logits = self.out(result['pooler_output'])
        # 返回结果
        return logits  # 因为后续用多分类损失函数,此处不需要用softmax转概率


if __name__ == '__main__':
    # 创建模型
    mybert = MyBertClassfier()
    # 获取数据
    train_dataloader, test_dataloader, dev_dataloader = build_all_dataloader()
    for batch_x, batch_y in train_dataloader:
        print(f"真实结果:{batch_y}")
        logits = mybert(batch_x)
        print(f"预测分数:{logits}")  # 最大分数对应的索引就是预测结果
        break
