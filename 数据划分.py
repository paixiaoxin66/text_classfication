import pandas as pd
from sklearn.model_selection import train_test_split

# 读取数据
df = pd.read_csv("data.csv", encoding="utf-8-sig")
df = df.dropna(subset=["category", "ask"]).reset_index(drop=True)

# 划分比例
train_ratio = 0.8
dev_ratio = 0.1
test_ratio = 0.1
random_state = 42

# 统计每个类别的样本数
counts = df["category"].value_counts()
rare_classes = counts[counts < 3].index.tolist()

# 分离稀有类别
rare_df = df[df["category"].isin(rare_classes)].copy()
main_df = df[~df["category"].isin(rare_classes)].copy()

# 如果 main_df 为空，直接随机划分
if len(main_df) == 0:
    train_df, temp_df = train_test_split(
        df, test_size=0.2, random_state=random_state
    )
    dev_df, test_df = train_test_split(
        temp_df, test_size=0.5, random_state=random_state
    )
else:
    # 先分 train 和 temp
    train_main, temp_main = train_test_split(
        main_df,
        test_size=(dev_ratio + test_ratio),
        random_state=random_state,
        stratify=main_df["category"]
    )
    # 再分 dev 和 test
    dev_df, test_df = train_test_split(
        temp_main,
        test_size=test_ratio / (dev_ratio + test_ratio),
        random_state=random_state,
        stratify=temp_main["category"]
    )
    # 稀有类别全部加入训练集
    train_df = pd.concat([train_main, rare_df], ignore_index=True)

# 打乱训练集
train_df = train_df.sample(frac=1, random_state=random_state).reset_index(drop=True)

# 保存
train_df.to_csv("train.csv", index=False, encoding="utf-8-sig")
dev_df.to_csv("dev.csv", index=False, encoding="utf-8-sig")
test_df.to_csv("test.csv", index=False, encoding="utf-8-sig")

# 打印分布
print("总样本数:", len(df))
print("train:", len(train_df), "dev:", len(dev_df), "test:", len(test_df))
print("\n训练集类别分布:\n", train_df["category"].value_counts())
print("\n验证集类别分布:\n", dev_df["category"].value_counts())
print("\n测试集类别分布:\n", test_df["category"].value_counts())