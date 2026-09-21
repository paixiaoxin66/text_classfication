import torch
from _01_p_config import Config
from _02_dataloader_utils import build_all_dataloader
from _03_bert_classifier_model import MyBertClassfier
from _04_bert_model_eval_utils import model_eval
from torch.nn.utils.prune import global_unstructured, L1Unstructured, remove

config = Config()

# 准备数据
_, _, dev_dataloader = build_all_dataloader()

# 准备模型
bert_model = MyBertClassfier()
num_layers = config.bert_config.num_hidden_layers

# 加载训练好的模型参数
bert_model.load_state_dict(torch.load(config.bert_model_save_path))
bert_model.to(config.device)
bert_model.eval()


def print_sparsity(model):
    """计算 query 权重稀疏度"""
    total_params = 0
    zero_params = 0
    layer_num = len(model.bert.encoder.layer)
    for i in range(layer_num):
        weight = model.bert.encoder.layer[i].attention.self.query.weight
        total_params += weight.numel()
        zero_params += (weight == 0).sum().item()
    r = zero_params / total_params if total_params > 0 else 0
    print(f"稀疏度: {r:.4f}")


def print_weights(model, rows=5, cols=5):
    print(f"\n（前 {rows}x{cols} 权重）：")
    print(model.bert.encoder.layer[0].attention.self.query.weight[:rows, :cols])


# 剪枝前
print("==================== 剪枝前 ====================")
print_weights(bert_model)
print_sparsity(bert_model)
acc, pre, rec, f1 = model_eval(dev_dataloader, bert_model, device=config.device)
print(f"剪枝前评估: 准确率:{acc:.4f}, 精确率:{pre:.4f}, 召回率:{rec:.4f}, f1:{f1:.4f}") # 剪枝前评估: 准确率:0.9797, 精确率:0.9808, 召回率:0.9811, f1:0.9809

# ============ 开始全局非结构化剪枝 ============
print("\n==================== 剪枝开始 ====================")
all_pru_params = [(bert_model.bert.encoder.layer[i].attention.self.query, "weight")
                  for i in range(num_layers)]

global_unstructured(
    parameters=all_pru_params,
    pruning_method=L1Unstructured,
    amount=0.3  # 剪掉 30%
)

# 固化剪枝（真正把 mask 应用进去）
for p, n in all_pru_params:
    remove(p, n)

print("==================== 剪枝结束 ====================")

# 剪枝后
print_weights(bert_model)
print_sparsity(bert_model)
acc, pre, rec, f1 = model_eval(dev_dataloader, bert_model, device=config.device)
print(f"剪枝后评估: 准确率:{acc:.4f}, 精确率:{pre:.4f}, 召回率:{rec:.4f}, f1:{f1:.4f}") # 剪枝后评估: 准确率:0.9803, 精确率:0.9814, 召回率:0.9817, f1:0.9815

# 保存剪枝后的模型
torch.save(bert_model.state_dict(), config.bert_pruning_save_path)
print(f"剪枝后模型已保存: {config.bert_pruning_save_path}")
