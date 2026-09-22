import os
import transformers
import torch


class Config():
    def __init__(self):
        # 项目根目录
        self.root_path = r'D:\PROJECT\DATA\_02_bert/'

        # 数据路径
        self.train_path = self.root_path + 'data/train.csv'
        self.test_path  = self.root_path + 'data/test.csv'
        self.dev_path   = self.root_path + 'data/dev.csv'
        self.class_path = self.root_path + 'data/class.txt'

        # BERT 预训练模型路径
        self.bert_base_chinese_path = self.root_path + 'bert-base-chinese'

        # 加载 tokenizer 和 config
        self.bert_tokenizer = transformers.BertTokenizer.from_pretrained(self.bert_base_chinese_path)
        self.bert_config    = transformers.BertConfig.from_pretrained(self.bert_base_chinese_path)
        self.bert_model     = transformers.BertModel.from_pretrained(self.bert_base_chinese_path)

        # 教师模型保存路径
        self.bert_model_save_path = self.root_path + 'model/bert_classifier_model.pt'

        # 学生蒸馏模型保存路径
        self.bilstm_distillation_save_path = r'D:\PROJECT\DATA\_04_bert_distillation\model/bert_distillation.pt'

        # 自动创建保存目录
        os.makedirs(os.path.dirname(self.bert_model_save_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.bilstm_distillation_save_path), exist_ok=True)

        # 超参数
        self.epochs = 5
        self.batch_size = 16
        self.lr = 2e-5
        self.max_len = 256
        self.class_num = 18

        # 设备
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"当前使用的设备: {self.device}")

        # 类别映射
        self.id2class = {index: line.strip() for index, line in enumerate(
            open(self.class_path, 'r', encoding='utf8'))}
        self.class2id = {v: k for k, v in self.id2class.items()}
        # 如果手动指定了 class_num，确保一致
        if self.class_num != len(self.id2class):
            print(f"[警告] class_num={self.class_num} 与 class.txt 中的类别数 {len(self.id2class)} 不一致，"
                  f"自动修正为 {len(self.id2class)}")
            self.class_num = len(self.id2class)

        # 蒸馏超参数
        self.embed_size = 128
        self.num_layers = 3
        self.lstm_hidden_size = 256
        self.dropout = 0.3
        self.lstm_lr = 0.001
        self.alpha = 0.7
        self.T = 2


if __name__ == '__main__':
    c = Config()
    print("类别数:", c.class_num)
    print("训练集路径:", c.train_path)
    print("id2class:", c.id2class)