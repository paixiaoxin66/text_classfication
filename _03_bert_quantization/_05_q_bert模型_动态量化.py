# 导包
import torch

from _01_q_config import Config
from _02_dataloader_utils import build_all_dataloader
from _03_bert_classifier_model import MyBertClassfier
from _04_bert_model_eval_utils import model_eval

# 创建配置对象
config = Config()
# 准备数据
_, _, dev_dataloader = build_all_dataloader()
# 准备模型
bert_model = MyBertClassfier()
# 加载训练好的模型参数
bert_model.load_state_dict(torch.load(config.bert_model_save_path))

# TODO 动态量化统一用CPU
bert_model.to(config.device)
# TODO 提前验证下当前模型的精度
current_acc, current_pre, current_rec, current_f1 = model_eval(dev_dataloader, bert_model, device=config.device)
print(f"量化前评估日志:准确率:{current_acc},"
      f"精确率:{current_pre},"
      f"召回率:{current_rec},"
      f"f1分数:{current_f1}")  # 准确率0.9796 精确率0.9808 召回率9811 f1分数0.9808

print('======================================================================================================')
print(f"模型开始量化")
# TODO TODO 开始量化模型
quantize_bert_model = torch.quantization.quantize_dynamic(
    model=bert_model,
    qconfig_spec={torch.nn.Linear},
    dtype=torch.qint8
)
print(f"模型量化结束")
# TODO 量化后验证下模型的精度
current_acc, current_pre, current_rec, current_f1 = model_eval(dev_dataloader, quantize_bert_model,
                                                               device=config.device)
print(f"量化后评估日志:准确率:{current_acc},"
      f"精确率:{current_pre},"
      f"召回率:{current_rec},"
      f"f1分数:{current_f1}")  # 准确率0.9726 精确率0.9747 召回率0.9746 f1分数0.9745

# TODO 保存量化后模型
torch.save(quantize_bert_model.state_dict(), config.bert_quantization_save_path)

print(f"模型保存成功")
