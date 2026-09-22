from _01_p_config import Config
from _03_bert_classifier_model import MyBertClassfier
import torch

config = Config()

bert_model = MyBertClassfier()
bert_model.load_state_dict(torch.load(config.bert_pruning_save_path))
bert_model.to(config.device)
bert_model.eval()   # 关键：预测前设置评估模式


def predict_fun(data):
    text = data['text']
    text_pt = config.bert_tokenizer(
        text, max_length=config.max_len, padding='max_length',
        truncation=True, return_tensors='pt'
    )
    # 字典必须用推导式
    text_pt = {k: v.to(config.device) for k, v in text_pt.items()}

    with torch.no_grad():
        logits = bert_model(text_pt)

    idx = torch.argmax(logits, dim=-1)[0].item()
    data['predict_class'] = config.id2class[idx]
    return data


if __name__ == '__main__':
    text = input('请您输入一个新闻:')
    data = {"text": text}
    result = predict_fun(data)
    print(result)