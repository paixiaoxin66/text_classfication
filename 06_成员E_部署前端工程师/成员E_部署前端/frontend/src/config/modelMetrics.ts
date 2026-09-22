/**
 * 模型真实实验指标(来自项目实验结果, 不伪造)
 * - 全部为同一真实测试集(877 条, 100% 真实数据)上的结果
 * - 特征: char_wb 字符级 n-gram(2-4) TF-IDF(传统模型) / BERT 原生 tokenizer
 * - 训练集: 30000 条(6893 真实 + 23107 增强), 18 类
 */
export interface ModelMetric {
  id: string;
  name: string;
  kind: '传统基线' | '深度学习';
  accuracy: number;   // 百分比
  macroF1: number;    // 百分比
  note: string;
}

export const MODEL_METRICS: ModelMetric[] = [
  {
    id: 'nb',
    name: '朴素贝叶斯',
    kind: '传统基线',
    accuracy: 72.41,
    macroF1: 68.26,
    note: 'TF-IDF + MultinomialNB',
  },
  {
    id: 'lr',
    name: '逻辑回归',
    kind: '传统基线',
    accuracy: 78.56,
    macroF1: 74.76,
    note: 'TF-IDF + LogisticRegression',
  },
  {
    id: 'svm',
    name: '线性SVM',
    kind: '传统基线',
    accuracy: 79.7,
    macroF1: 75.87,
    note: 'TF-IDF + LinearSVC(最强传统基线)',
  },
  {
    id: 'rf',
    name: '随机森林',
    kind: '传统基线',
    accuracy: 76.4,
    macroF1: 72.44,
    note: 'TF-IDF + chi2选8000特征 + RandomForest(200棵)',
  },
  {
    id: 'fasttext',
    name: 'FastText',
    kind: '传统基线',
    accuracy: 71.95,
    macroF1: 67.59,
    note: '子词n-gram + 平均嵌入(最快, 训练69s)',
  },
  {
    id: 'bert',
    name: 'BERT',
    kind: '深度学习',
    accuracy: 85.4,
    macroF1: 84.43,
    note: 'bert-base-chinese 微调(主模型)',
  },
];

export const DATASET_STATS = {
  raw: 9043,
  cleaned: 8950,
  train: 30000,
  trainReal: 6893,
  trainAug: 23107,
  val: 855,
  test: 877,
  classes: 18,
  augRatio: 0.77,
  dupRate: 0.0,
};

export const CURRENT_MODEL = 'bert-base-chinese 微调';
export const CURRENT_ACC = 85.4;
export const CURRENT_F1 = 84.43;
