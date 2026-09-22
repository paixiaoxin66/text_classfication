import transformers
import torch


class Config():
    def __init__(self):
        # 各种路径
        # TODO 1.原始数据路径（请根据你的实际项目路径修改 root_path）
        self.root_path = r'D:\PROJECT\DATA/'
        self.train_path = self.root_path + '_02_bert/data/train.csv'
        self.test_path = self.root_path + '_02_bert/data/test.csv'
        self.dev_path = self.root_path + '_02_bert/data/dev.csv'
        # 停用词和类别路径
        self.stop_words_path = self.root_path + '_02_bert/data/stopwords.txt'
        self.class_path = self.root_path + '_02_bert/data/class.txt'

        # TODO 2.随机森林相关路径（如不使用可忽略）
        self.process_train_path = self.root_path + '_02_rf/processed_data/train_process.txt'
        self.process_test_path = self.root_path + '_02_rf/processed_data/test_process.txt'
        self.process_dev_path = self.root_path + '_02_rf/processed_data/dev_process.txt'
        self.rf_save_model_path = self.root_path + '_02_rf/model/rf.pkl'
        self.tfidf_save_path = self.root_path + '_02_rf/model/tfidf.pkl'

        # TODO 3.fasttext相关路径（如不使用可忽略）
        self.process_train_path_chars = self.root_path + '_03_fasttext/processed_data/train_process_chars.txt'
        self.process_test_path_chars = self.root_path + '_03_fasttext/processed_data/test_process_chars.txt'
        self.process_dev_path_chars = self.root_path + '_03_fasttext/processed_data/dev_process_chars.txt'
        self.process_train_path_words = self.root_path + '_03_fasttext/processed_data/train_process_words.txt'
        self.process_test_path_words = self.root_path + '_03_fasttext/processed_data/test_process_words.txt'
        self.process_dev_path_words = self.root_path + '_03_fasttext/processed_data/dev_process_words.txt'
        self.ft_char_default_model_path = self.root_path + '_03_fasttext/model/ft_char_default.bin'
        self.ft_char_auto_model_path = self.root_path + '_03_fasttext/model/ft_char_auto.bin'
        self.ft_word_default_model_path = self.root_path + '_03_fasttext/model/ft_word_default.bin'
        self.ft_word_auto_model_path = self.root_path + '_03_fasttext/model/ft_word_auto.bin'

        # 分类词表：id -> 类别名
        self.id2class = {index: line.strip() for index, line in enumerate(
            open(self.class_path, 'r', encoding='utf8'))}
        # 类别名 -> id
        self.class2id = {v: k for k, v in self.id2class.items()}

        # TODO 4.bert相关路径和各种超参数
        # 路径（请确认本地已有 bert-base-chinese 模型）
        self.bert_base_chinese_path = self.root_path + '_02_bert/bert-base-chinese'
        self.bert_tokenizer = transformers.BertTokenizer.from_pretrained(self.bert_base_chinese_path)
        self.bert_model = transformers.BertModel.from_pretrained(self.bert_base_chinese_path)
        self.bert_model_save_path = self.root_path + '_02_bert/model/bert_classifier_model.pt'

        # 超参数
        self.epochs = 3
        self.batch_size = 32
        self.lr = 0.00005
        self.max_len = 256          # 可根据投诉文本长度适当增大，如 64/128
        self.bert_config = transformers.BertConfig.from_pretrained(self.bert_base_chinese_path)
        self.class_num = len(self.id2class)   # 自动等于 18

        # 设备：动态量化必须用 CPU
        self.device = torch.device('cpu')

        # TODO 4.1 量化相关内容
        self.bert_quantization_save_path = r"D:\PROJECT\DATA\_03_bert_quantization\model/bert_quantization.pt"


if __name__ == '__main__':
    c = Config()
    print(c.bert_base_chinese_path)
    print(c.bert_config.hidden_size)
    print("类别数:", c.class_num)
    print("id2class:", c.id2class)
    print(c.bert_quantization_save_path)