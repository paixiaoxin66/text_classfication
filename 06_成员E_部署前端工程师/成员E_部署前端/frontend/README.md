# 樱花主题前端（消费者投诉文本分类系统）

React 18 + TypeScript + Vite + Tailwind CSS v4 + Framer Motion + Lucide Icons

## 目录结构

```
frontend/
├── index.html
├── package.json / vite.config.ts / tsconfig.*
├── .env.development          # API 地址与 mock 开关
├── public/
│   ├── sakura.svg            # 站点图标
│   └── assets/images/
│       ├── anime-girl.svg    # 二次元少女占位图(可直接替换)
│       └── anime-girl.png    # 【预留】放真实图片后自动使用
└── src/
    ├── main.tsx / App.tsx / index.css
    ├── api/classification.ts     # API 层(唯一需要对接后端的地方)
    ├── config/
    │   ├── categories.ts         # 18 类标签与说明
    │   └── modelMetrics.ts       # 模型真实指标(实验数据, 勿伪造)
    ├── types/classification.ts   # 类型定义
    ├── components/               # Header/Sidebar/Sakura/Input/Loading/Top3/概率列表/Footer
    └── pages/                    # Home/Statistics/Categories/ModelInfo/History
```

## 启动步骤

```bash
cd frontend
npm install        # 首次
npm run dev        # 开发服务器 http://localhost:5173
```

## 后端启动（分类 API）

```bash
# 在项目根目录(hemao_scraper)
uv sync            # 安装 fastapi/uvicorn
uv run uvicorn api_server:app --host 0.0.0.0 --port 8000
# 或: .venv\Scripts\python.exe -m uvicorn api_server:app --port 8000
```

后端加载 `data/out/bert_model`（微调后的 BERT），接口：

```
POST /api/v1/classify
请求:  {"text": "投诉内容"}
响应:  {
  "text": "投诉内容",
  "predictions": [
    {"label": "教育", "probability": 0.9947},   # 18 项, 已按概率降序
    ...
  ],
  "model": "bert-base-chinese"
}
GET  /health   -> {"status": "ok", "model_loaded": true}
```

## API 地址配置

- 开发环境：`frontend/.env.development` 中 `VITE_API_BASE_URL=http://localhost:8000`
  （同时 Vite 已将 `/api` 代理到 8000 端口，二选一即可）
- 演示模式：`VITE_USE_MOCK=true` 时后端不可用也返回演示数据（UI 上明确标注「演示数据」，
  非真实模型预测；后端就绪后改回 `false` 即可，UI 层无需改动）

## 数据来源（真实，不伪造）

| 模型 | 准确率 | Macro-F1 |
|---|---|---|
| 朴素贝叶斯 | 72.41% | 68.26% |
| 逻辑回归 | 78.56% | 74.76% |
| 线性SVM | 79.70% | 75.87% |
| **BERT(主模型)** | **85.40%** | **84.43%** |

- 训练集 30000 条（6893 真实 + 23107 增强），验证/测试 100% 真实
- 来源：`data/out_ablation/char_wb` 与 `data/out/bert_report.txt`（seed=42 可复现）

## 替换二次元少女图片

把真实图片命名为 `anime-girl.png` 放到 `public/assets/images/` 即可（当前使用 SVG 占位）。

## 页面背景图（参考图）

- 源文件：`素材/background.png`（1536×1024 横版场景）
- 已优化并放入 `public/assets/images/background.jpg`（1.8MB → 0.14MB）
- `App.tsx` 的 `.bg-scene` 图层以 `object-fit: cover` 整页铺底，
  左侧叠加 `linear-gradient` 遮罩保证文字可读，右侧少女自然融入背景
- 换图：替换 `public/assets/images/background.jpg` 即可，无需改代码

