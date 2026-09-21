from _01_d_config import Config
from _03_distill_bilstm_model import MyBiLSTM
import torch

config = Config()

bilstm = MyBiLSTM()
bilstm.load_state_dict(torch.load(config.bilstm_distillation_save_path))
bilstm.to(config.device)
bilstm.eval()


def predict_fun(data):
    text = data['text']
    text_pt = config.bert_tokenizer(
        text, max_length=config.max_len, padding='max_length',
        truncation=True, return_tensors='pt'
    )
    text_pt = {k: v.to(config.device) for k, v in text_pt.items()}

    with torch.no_grad():
        logits = bilstm(text_pt)

    idx = torch.argmax(logits, dim=-1)[0].item()
    data['predict_class'] = config.id2class[idx]
    return data


if __name__ == '__main__':
    text = input('请您输入一段文本:')
    data = {"text": text}
    print(predict_fun(data))