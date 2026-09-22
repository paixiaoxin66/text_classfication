import pandas as pd
class Config():
    def __init__(self):
        # 根路径，按你自己的改
        self.root_path = r'D:\PROJECT\DATA\_01_rf/'

        # 原始数据路径：现在是 csv，列名 category,ask
        self.train_path = self.root_path + 'data/train.csv'
        self.dev_path = self.root_path + 'data/dev.csv'
        self.test_path = self.root_path + 'data/test.csv'

        # 停用词和类别路径
        self.stop_words_path = self.root_path + 'data/stopwords.txt'
        self.class_path = self.root_path + 'data/class.txt'

        # 分词后数据存放路径
        self.process_train_path = self.root_path + 'processed_data/train_process.csv'
        self.process_dev_path = self.root_path + 'processed_data/dev_process.csv'
        self.process_test_path = self.root_path + 'processed_data/test_process.csv'

        # 模型保存路径
        self.rf_save_model_path = self.root_path + 'model/rf.pkl'
        self.tfidf_save_path = self.root_path + 'model/tfidf.pkl'
        self.label_encoder_path = self.root_path + 'model/label_encoder.pkl'






if __name__ == '__main__':
    c = Config()
    print(c.train_path)
    print(c.dev_path)
    print(c.test_path)
    train = pd.read_csv('data/train.csv', encoding='utf-8-sig')
    test = pd.read_csv('data/test.csv', encoding='utf-8-sig')

    # 看文本是否完全重合
    overlap = pd.merge(train, test, on='ask', how='inner')
    print(f"训练集和测试集完全重复的文本数量: {len(overlap)}")
    # 看文本长度分布，如果都很短，说明特征太容易抽取
    print(train['ask'].str.len().describe())