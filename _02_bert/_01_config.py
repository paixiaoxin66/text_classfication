import transformers
import torch


class Config():
    def __init__(self):
        # TODO 1.原始数据路径 (修改为 csv 格式)
        self.root_path = r'D:\PROJECT\DATA\_02_bert/'
        self.train_path = self.root_path + 'data/train.csv'
        self.test_path = self.root_path + 'data/test.csv'
        self.dev_path = self.root_path + 'data/dev.csv'

        # 停用词和类别路径
        self.class_path = self.root_path + 'data/class.txt'

        # TODO 2.BERT相关路径和超参数
        # 路径 (注意：把你下载的 bert 文件夹名字改成 bert-base-chinese)
        self.bert_base_chinese_path = self.root_path + 'bert-base-chinese'

        # 提前加载 bert 的 tokenizer 和 config
        self.bert_tokenizer = transformers.BertTokenizer.from_pretrained(self.bert_base_chinese_path)
        self.bert_config = transformers.BertConfig.from_pretrained(self.bert_base_chinese_path)
        self.bert_model = transformers.BertModel.from_pretrained(self.bert_base_chinese_path)

        # bert模型保存路径
        self.bert_model_save_path = self.root_path + 'model/bert_classifier_model.pt'

        # 超参数 (根据你的数据量修改)
        self.epochs = 3
        self.batch_size = 16  # 显存不够可以调小，如 8 或 16
        self.lr = 2e-5  # BERT 微调常用学习率
        self.max_len = 256  # 你的文本平均 142 字，最大 271 字，256 可以覆盖绝大部分
        self.class_num = 18  # 你的截图显示是 18 个类别，可以在这里硬编码，也可以后面动态获取

        # 提前设置设备
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"当前使用的设备: {self.device}")


if __name__ == '__main__':
    c = Config()
    print(c.bert_base_chinese_path)
    print(c.bert_config.hidden_size)