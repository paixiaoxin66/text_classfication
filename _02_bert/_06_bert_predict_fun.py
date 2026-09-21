import torch
from _01_config import Config
from _03_bert_classifier_model import MyBertClassfier

config = Config()

# 创建模型结构
bert_model = MyBertClassfier()
# 加载权重 (注意 map_location 保证在 CPU 上也能加载)
bert_model.load_state_dict(torch.load(config.bert_model_save_path, map_location=config.device))
bert_model.to(config.device)
bert_model.eval()

# 动态读取 class.txt
with open(config.class_path, 'r', encoding='utf-8') as f:
    id2class = {index: line.strip() for index, line in enumerate(f)}


def predict_fun(data):
    text = data['text']
    # tokenizer 编码
    text_pt = config.bert_tokenizer(
        text,
        max_length=config.max_len,
        padding='max_length',
        truncation=True,
        return_tensors='pt'
    )
    # TODO 修复：text_pt 是字典，需要遍历字典移入设备
    text_pt = {k: v.to(config.device) for k, v in text_pt.items()}

    with torch.no_grad():
        logits = bert_model(text_pt)
        y_pred_idx = torch.argmax(logits, dim=-1)
        idx = y_pred_idx[0].item()
        y_pred_class = id2class[idx]
        data['predict_class'] = y_pred_class
    return data


if __name__ == '__main__':
    text = input('请输入一段文本：')
    data = {"text": text}
    result = predict_fun(data)
    print(result)