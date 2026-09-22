# 导包
from _01_q_config import Config
from _03_bert_classifier_model import MyBertClassfier
import torch

# 创建对象
config = Config()

# 创建空模型
bert_model = MyBertClassfier()
# 先把初始模型量化为qint8
quantize_bert_model = torch.quantization.quantize_dynamic(
    model=bert_model,
    qconfig_spec={torch.nn.Linear},
    dtype=torch.qint8
)
# 读取本地的量化参数字典，加载到量化后的模型中
quantize_bert_model.load_state_dict(torch.load(config.bert_quantization_save_path))
# 把【量化模型】放到CPU设备上，并设置为评估模式（极其重要！）
quantize_bert_model.to(config.device)
quantize_bert_model.eval()


def predict_fun(data):
    # 获取文本数据
    text = data['text']
    # tokenizer把文本数据转换为数值特征
    text_pt = config.bert_tokenizer(text, max_length=config.max_len, padding='max_length', truncation=True,
                                    return_tensors='pt')
    # 把数据放到设备上（修复了字典没有 .to() 方法的Bug）
    text_pt = {k: v.to(config.device) for k, v in text_pt.items()}

    # 模型开始预测（关闭梯度跟踪，使用正确的 quantize_bert_model）
    with torch.no_grad():
        logits = quantize_bert_model(text_pt)

    # 最大分数对应的索引就是预测结果
    y_pred_idx = torch.argmax(logits, dim=-1)
    idx = y_pred_idx[0].item()
    # 根据索引获取对应标签
    y_pred_class = config.id2class[idx]
    # 拼接到data中
    data['predict_class'] = y_pred_class
    # 返回
    return data


if __name__ == '__main__':
    # 模拟准备json格式数据
    text = input('请您输入一个新闻:')
    data = {"text": text}
    # 模拟调用API
    result = predict_fun(data)
    print(result)