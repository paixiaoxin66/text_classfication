# 导包
import torch
from _01_d_config import Config

c = Config()


# TODO 自定义模型1个继承2个重写
class MyBiLSTM(torch.nn.Module):
    # 初始化方法
    def __init__(self):
        super().__init__()
        # 提前向量化
        self.embedding = torch.nn.Embedding(num_embeddings=c.bert_config.vocab_size, embedding_dim=c.embed_size)
        # 隐藏层用双向的LSTM
        self.bilstm = torch.nn.LSTM(input_size=c.embed_size, hidden_size=c.lstm_hidden_size, num_layers=c.num_layers,
                                    bidirectional=True, batch_first=True)
        # 设置随机失活层
        self.dropout = torch.nn.Dropout(p=c.dropout)
        # bilstm输出的256*2维度不符合10分类结果要求,自己额外添加线性层转换
        self.linear = torch.nn.Linear(c.lstm_hidden_size * 2, c.class_num)


    # 前向传播
    def forward(self,x):
        # 此处x包含:input_ids,token_type_ids,attention_mask三部分
        # todo 1.单独input_ids和attention_mask
        input_ids = x['input_ids']
        attention_mask = x['attention_mask']
        # todo 2.词嵌入层生成词向量
        # input_ids形状: [batch_size,seq_len]
        # all_embed: [batch_size,seq_len,embed_size]
        all_embed = self.embedding(input_ids)
        # todo 3.因为lstm不需要bert的特殊字符,过滤: [CLS],[SEP],[PAD]词向量(本质都是置为0)
        cls_token_id = 101
        sep_token_id = 102
        # 拿到删除cls和sep的布尔张量
        drop_cls_sep_mask = (input_ids != cls_token_id) & (input_ids != sep_token_id)
        # 获取去除cls和sep以及pad后的注意力: 删除cls和sep的布尔张量和attention_mask相乘获取新的掩码注意力
        valid_mask = drop_cls_sep_mask * attention_mask
        # 拿着整体词向量 和 valid_mask ,有效位置的保留原始词向量,无效位置改为0(cls和sep以及pad)
        # valid_mask形状: [batch_size,seq_len,1]
        valid_mask = valid_mask.unsqueeze(-1)
        valid_embed = all_embed * valid_mask

        # TODO 4.双向lstm开始前向传播
        # lstm_out形状: [batch_size,seq_len,hidden_size_lstm * 2]
        lstm_out, _ = self.bilstm(valid_embed)

        # todo 5.平均池化,对整个句子"有效字符"进行平均池化
        # 先获取所有有效位的输出
        # valid_lstm_out形状: [batch_size,seq_len,hidden_size_lstm * 2]
        valid_lstm_out = lstm_out * valid_mask

        #
        # 求和  sum_hidden形状: [batch_size,hidden_size_lstm*2]
        sum_hidden = valid_lstm_out.sum(dim=1)
        # 求个数  valid_token_cnt形状: [batch_size,1]
        valid_token_cnt = valid_mask.sum(dim=1)
        # 平均池化
        avg_hidden = sum_hidden/valid_token_cnt

        # todo 6.随机失活
        avg_hidden = self.dropout(avg_hidden)

        # todo 7.线性变化
        logits = self.linear(avg_hidden)

        # 最后返回
        return logits


if __name__ == '__main__':
    bilstm = MyBiLSTM()
    for i in bilstm.named_parameters():
        print(i)
