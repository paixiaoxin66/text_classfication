import pandas as pd

# 读取第一个数据集
df = pd.read_csv("train_augmented.csv", encoding="utf-8-sig")

# 去掉列名可能存在的空格
df.columns = df.columns.str.strip()

# 如果只想要未增强的原始数据，取消下面这行注释
# df = df[df["is_aug"] == 0]

# 只保留 category 和 text，并改成和 1.xlsx 一样的列名
out = df[["category", "text"]].copy()
out.columns = ["category", "ask"]

# 可选：简单清洗文本
out["category"] = out["category"].astype(str).str.strip()
out["ask"] = (
    out["ask"]
    .astype(str)
    .str.replace(r"<br\s*/?>", " ", regex=True)  # 去掉 <br>
    .str.replace(r"\s+", " ", regex=True)        # 多个空白合成一个空格
    .str.strip()
)

# 删除空值和重复行
out = out.dropna(subset=["category", "ask"])
out = out[(out["category"] != "") & (out["ask"] != "")]
out = out.drop_duplicates().reset_index(drop=True)

# 保存成新文件，格式和 1.xlsx 一样
out.to_csv("data.csv", index=False, encoding='utf-8-sig')

print(out.head())
print("总行数：", len(out))