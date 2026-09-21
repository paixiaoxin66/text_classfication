from _01_p_config import Config
import torch

config = Config()


class MyBertClassfier(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.bert = config.bert_model
        self.out = torch.nn.Linear(config.bert_config.hidden_size, config.class_num)

    def forward(self, batch_x):
        result = self.bert(**batch_x)
        logits = self.out(result['pooler_output'])
        return logits


if __name__ == '__main__':
    mybert = MyBertClassfier()
    print(mybert)