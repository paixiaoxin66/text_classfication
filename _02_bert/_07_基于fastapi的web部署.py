# 导包
import sys
import os
import time

# 保证能导入同目录下的 _05_rf_predict_fun
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# todo 导入写好的预测函数
from _06_bert_predict_fun import predict_fun


# todo 1.创建 FastAPI 应用
app = FastAPI(title="NLP News Classifier", version="1.0")


# todo 2.定义请求体模型
class NewsRequest(BaseModel):
    text: str


# todo 3.二次元风格页面(樱花 / 软萌风)
INDEX_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌸 二次元投诉分类娘 · 文本分类系统</title>
    <link href="https://fonts.googleapis.com/css2?family=ZCOOL+KuaiLe&family=Zen+Maru+Gothic:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        :root {
            --pink: #ff7eb3;
            --pink-deep: #ff5c8a;
            --purple: #b39ddb;
            --purple-deep: #9575cd;
            --blue: #8ecae6;
            --mint: #a8e6cf;
            --cream: #fff7fb;
            --text-main: #5b4a6a;
            --text-sub: #9b8aa8;
            --card-border: #ffd6e8;
            --shadow-soft: 0 10px 30px rgba(255, 126, 179, 0.25);
            --shadow-card: 0 14px 40px rgba(179, 157, 219, 0.25);
        }

        body {
            font-family: 'Zen Maru Gothic', 'ZCOOL KuaiLe', 'Microsoft YaHei', sans-serif;
            min-height: 100vh;
            position: relative;
            overflow-x: hidden;
            color: var(--text-main);
            background: linear-gradient(135deg, #ffe3f1 0%, #e8e0ff 50%, #dff3ff 100%);
            background-attachment: fixed;
        }

        /* 柔光云朵背景 */
        .bg-blob {
            position: fixed;
            border-radius: 50%;
            filter: blur(60px);
            opacity: 0.55;
            z-index: 0;
            pointer-events: none;
        }
        .blob-1 { width: 380px; height: 380px; background: #ffb3d9; top: -80px; left: -80px; animation: float 9s ease-in-out infinite; }
        .blob-2 { width: 320px; height: 320px; background: #b3d9ff; bottom: -60px; right: -60px; animation: float 11s ease-in-out infinite reverse; }
        .blob-3 { width: 260px; height: 260px; background: #d9b3ff; top: 40%; right: 10%; animation: float 13s ease-in-out infinite; }

        @keyframes float {
            0%, 100% { transform: translateY(0) scale(1); }
            50% { transform: translateY(-30px) scale(1.08); }
        }

        /* 樱花花瓣 */
        .petal-layer {
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            overflow: hidden;
            pointer-events: none;
            z-index: 1;
        }
        .petal {
            position: absolute;
            top: -40px;
            font-size: 20px;
            opacity: 0.85;
            animation: fall linear infinite;
        }
        @keyframes fall {
            0% { transform: translateY(-40px) rotate(0deg); opacity: 0; }
            10% { opacity: 0.9; }
            100% { transform: translateY(105vh) translateX(60px) rotate(360deg); opacity: 0; }
        }

        .container {
            position: relative;
            z-index: 2;
            max-width: 960px;
            margin: 0 auto;
            padding: 40px 20px 100px;
        }

        /* 标题区 */
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 34px 24px;
            background: rgba(255, 255, 255, 0.72);
            backdrop-filter: blur(12px);
            border: 3px solid #fff;
            border-radius: 32px;
            box-shadow: var(--shadow-card);
            position: relative;
        }

        .mascot {
            font-size: 46px;
            display: inline-block;
            animation: bounce 2.4s ease-in-out infinite;
        }
        @keyframes bounce {
            0%, 100% { transform: translateY(0) rotate(-4deg); }
            50% { transform: translateY(-12px) rotate(4deg); }
        }

        h1 {
            font-family: 'ZCOOL KuaiLe', 'Zen Maru Gothic', sans-serif;
            font-size: 34px;
            margin: 6px 0 8px;
            background: linear-gradient(135deg, var(--pink-deep), var(--purple-deep));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: 1px;
        }

        .subtitle {
            color: var(--text-sub);
            font-size: 14px;
        }
        .subtitle .heart { color: var(--pink-deep); }

        /* 输入卡片 */
        .card {
            background: rgba(255, 255, 255, 0.82);
            backdrop-filter: blur(12px);
            border: 3px solid #fff;
            border-radius: 28px;
            padding: 28px;
            margin-bottom: 26px;
            box-shadow: var(--shadow-card);
        }

        .card-head {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 16px;
            font-weight: 700;
            font-size: 16px;
            color: var(--purple-deep);
        }
        .card-head .tag {
            font-size: 12px;
            font-weight: 400;
            color: #fff;
            background: linear-gradient(135deg, var(--pink), var(--purple));
            padding: 3px 12px;
            border-radius: 999px;
        }

        textarea {
            width: 100%;
            min-height: 170px;
            padding: 20px;
            background: var(--cream);
            border: 3px dashed var(--card-border);
            border-radius: 20px;
            color: var(--text-main);
            font-family: 'Zen Maru Gothic', 'Microsoft YaHei', sans-serif;
            font-size: 15px;
            line-height: 1.8;
            resize: vertical;
            transition: all 0.3s;
        }
        textarea:focus {
            outline: none;
            border-color: var(--pink);
            border-style: solid;
            background: #fff;
            box-shadow: var(--shadow-soft);
        }
        textarea::placeholder { color: #c9b8d4; }

        .button-group {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 14px;
            margin-top: 20px;
        }

        button {
            padding: 16px;
            font-family: 'ZCOOL KuaiLe', 'Zen Maru Gothic', sans-serif;
            font-size: 17px;
            cursor: pointer;
            border-radius: 999px;
            border: none;
            transition: all 0.25s;
            letter-spacing: 1px;
        }

        .btn-execute {
            color: #fff;
            background: linear-gradient(135deg, var(--pink), var(--purple));
            box-shadow: 0 8px 20px rgba(255, 126, 179, 0.45);
        }
        .btn-execute:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 12px 26px rgba(255, 92, 138, 0.55);
        }
        .btn-execute:active { transform: translateY(0) scale(0.99); }
        .btn-execute:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

        .btn-clear {
            color: var(--purple-deep);
            background: #fff;
            border: 3px solid var(--card-border);
        }
        .btn-clear:hover {
            background: #fff0f7;
            border-color: var(--pink);
            transform: translateY(-3px);
        }

        /* 结果区 */
        .output-section {
            display: none;
            animation: pop 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .output-section.show { display: block; }

        @keyframes pop {
            from { opacity: 0; transform: translateY(24px) scale(0.96); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }

        .output-header {
            font-family: 'ZCOOL KuaiLe', sans-serif;
            font-size: 20px;
            color: var(--pink-deep);
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .result-card {
            position: relative;
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(12px);
            border: 3px solid var(--card-border);
            border-radius: 26px;
            padding: 26px;
            box-shadow: var(--shadow-card);
        }
        .result-card.error-card { border-color: #ffb3b3; }

        .result-row {
            display: flex;
            gap: 14px;
            margin-bottom: 14px;
            padding: 14px 16px;
            background: linear-gradient(135deg, #fff5fa, #f3f0ff);
            border-radius: 18px;
        }

        .result-label {
            color: var(--purple-deep);
            font-weight: 700;
            min-width: 120px;
            flex-shrink: 0;
        }

        .result-value {
            color: var(--text-main);
            flex: 1;
            word-break: break-word;
            line-height: 1.7;
        }

        .classification-result {
            font-family: 'ZCOOL KuaiLe', sans-serif;
            font-size: 28px;
            color: var(--pink-deep);
            text-shadow: 0 2px 10px rgba(255, 126, 179, 0.5);
        }

        .time-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 9px 18px;
            margin-top: 14px;
            border-radius: 999px;
            font-size: 14px;
            color: var(--purple-deep);
            background: linear-gradient(135deg, #ffe3f1, #e8e0ff);
            border: 2px solid #fff;
        }
        .time-badge::before { content: '⏱️'; }

        /* 状态栏 */
        .status-bar {
            position: fixed;
            bottom: 0; left: 0; right: 0;
            padding: 11px 22px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12.5px;
            color: #fff;
            background: linear-gradient(90deg, var(--pink), var(--purple), var(--blue));
            z-index: 100;
        }
        .status-item { display: flex; align-items: center; gap: 8px; }

        .status-indicator {
            width: 9px; height: 9px;
            border-radius: 50%;
            background: #fff;
            animation: pulse 1.6s ease-in-out infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.8); }
        }

        ::-webkit-scrollbar { width: 10px; }
        ::-webkit-scrollbar-track { background: #fff0f7; }
        ::-webkit-scrollbar-thumb { background: var(--pink); border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--pink-deep); }

        @media (max-width: 640px) {
            h1 { font-size: 26px; }
            .button-group { grid-template-columns: 1fr; }
            .result-label { min-width: 90px; }
        }
    </style>
</head>
<body>
    <div class="bg-blob blob-1"></div>
    <div class="bg-blob blob-2"></div>
    <div class="bg-blob blob-3"></div>
    <div class="petal-layer" id="petalLayer"></div>

    <div class="container">
        <div class="header">
            <div class="mascot">🌸</div>
            <h1>二次元投诉分类娘</h1>
            <div class="subtitle">✧ Bert ✧ 把你输入的投诉文本分好类哒~ <span class="heart">♥</span></div>
        </div>

        <div class="card">
            <div class="card-head">📝 请输入投诉文本 <span class="tag">Text Input</span></div>
            <textarea id="text" placeholder="在这里粘贴或输入一段投诉内容吧~&#10;例如：酒店订了没住，结果美团扣了全款，找客服还不退。;（小提示：按下 Ctrl + Enter 也能提交哦 ✧）"></textarea>

            <div class="button-group">
                <button type="button" id="btnExecute" class="btn-execute">✨ 开始分析 (๑•̀ㅂ•́)و✧</button>
                <button type="button" class="btn-clear" onclick="clearText()">🍃 清空</button>
            </div>
        </div>

        <div class="output-section" id="outputSection">
            <div class="output-header" id="outputHeader">🎀 分析完成啦～</div>
            <div class="result-card" id="resultCard">
                <div class="result-row">
                    <div class="result-label">📜 输入内容</div>
                    <div class="result-value" id="resultText"></div>
                </div>
                <div class="result-row" id="predictRow">
                    <div class="result-label">🔮 分类结果</div>
                    <div class="result-value classification-result" id="resultClass"></div>
                </div>
                <div class="time-badge">
                    响应时间：<span id="resultTime">0</span> ms
                </div>
            </div>
        </div>
    </div>

    <div class="status-bar">
        <div class="status-item">
            <div class="status-indicator"></div>
            <span>分类娘在线中 ♪</span>
        </div>
        <div class="status-item">
            <span>框架 FastAPI · 模型 随机森林</span>
        </div>
        <div class="status-item">
            <span>端口 9092</span>
        </div>
    </div>

    <script>
        const btnExecute = document.getElementById('btnExecute');
        const textarea = document.getElementById('text');
        const outputSection = document.getElementById('outputSection');
        const outputHeader = document.getElementById('outputHeader');
        const resultCard = document.getElementById('resultCard');
        const resultText = document.getElementById('resultText');
        const resultClass = document.getElementById('resultClass');
        const resultTime = document.getElementById('resultTime');
        const predictRow = document.getElementById('predictRow');

        // 生成飘落的樱花花瓣
        (function makePetals() {
            const layer = document.getElementById('petalLayer');
            const flowers = ['🌸', '🌸', '🌸', '💮', '🌺'];
            for (let i = 0; i < 22; i++) {
                const p = document.createElement('div');
                p.className = 'petal';
                p.textContent = flowers[Math.floor(Math.random() * flowers.length)];
                p.style.left = Math.random() * 100 + 'vw';
                p.style.fontSize = (14 + Math.random() * 16) + 'px';
                p.style.animationDuration = (7 + Math.random() * 8) + 's';
                p.style.animationDelay = (Math.random() * 10) + 's';
                layer.appendChild(p);
            }
        })();

        function clearText() {
            textarea.value = '';
            textarea.focus();
            outputSection.classList.remove('show');
        }

        async function execute() {
            const text = textarea.value.trim();
            if (!text) {
                showError('输入文本不能为空哦～');
                return;
            }

            btnExecute.disabled = true;
            btnExecute.textContent = '⏳ 分析中...';
            const start = performance.now();

            try {
                const resp = await fetch('/api/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: text })
                });
                const data = await resp.json();
                const roundTrip = (performance.now() - start).toFixed(2);

                if (data.success) {
                    showSuccess(text, data.predict_class, data.response_time_ms, roundTrip);
                } else {
                    showError(data.error || '预测失败', data.response_time_ms);
                }
            } catch (e) {
                showError('请求失败: ' + e.message);
            } finally {
                btnExecute.disabled = false;
                btnExecute.textContent = '✨ 开始分析 (๑•̀ㅂ•́)و✧';
            }
        }

        function showSuccess(text, predictClass, serverMs, roundTripMs) {
            outputHeader.textContent = '🎀 分析完成啦～';
            resultCard.classList.remove('error-card');
            resultCard.style.borderColor = '';
            predictRow.style.display = 'flex';

            resultText.textContent = text.length > 300 ? text.slice(0, 300) + '...' : text;
            resultClass.textContent = predictClass;
            resultTime.textContent = serverMs;
            if (roundTripMs !== undefined) {
                resultTime.textContent = serverMs + ' (服务端) / ' + roundTripMs + ' (往返)';
            }
            outputSection.classList.add('show');
        }

        function showError(msg, serverMs) {
            outputHeader.textContent = '💦 出错了呜呜～';
            resultCard.classList.add('error-card');
            predictRow.style.display = 'none';

            resultText.textContent = msg;
            resultTime.textContent = serverMs !== undefined ? serverMs : '-';
            outputSection.classList.add('show');
        }

        btnExecute.addEventListener('click', execute);
        textarea.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') { execute(); }
        });
    </script>
</body>
</html>
"""


# todo 4.页面路由
@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=INDEX_HTML)


# todo 5.预测接口:接收新闻文本 -> 调用 predict_fun -> 返回结果 + 响应时间
@app.post("/api/predict")
async def api_predict(req: NewsRequest):
    text = (req.text or "").strip()
    if not text:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "输入文本不能为空"},
        )

    start_time = time.perf_counter()
    try:
        # todo 5.1 组装数据并调用写好的预测函数
        data = {"text": text}
        result = predict_fun(data)
        # todo 5.2 计算响应时间(ms)
        response_time = round((time.perf_counter() - start_time) * 1000, 2)
        # todo 5.3 返回结果
        return {
            "success": True,
            "text": result.get("text", text),
            "predict_class": result.get("predict_class"),
            "response_time_ms": response_time,
        }
    except Exception as e:
        response_time = round((time.perf_counter() - start_time) * 1000, 2)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"预测失败: {str(e)}",
                "response_time_ms": response_time,
            },
        )


if __name__ == '__main__':
    print("=" * 50)
    print("新闻文本分类系统启动中... (FastAPI 二次元版)")
    print("=" * 50)
    print("访问地址: http://127.0.0.1:9092")
    print("接口文档: http://127.0.0.1:9092/docs")
    print("=" * 50)
    # uvicorn.run(app, host='0.0.0.0', port=9092)
    uvicorn.run(app, host='127.0.0.1', port=9092)
