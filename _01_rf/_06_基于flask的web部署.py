from flask import Flask, render_template_string, request
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# todo 导包
from _05_rf_predict_fun import predict_fun


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    input_text = ''
    response_time = None

    if request.method == 'POST':
        input_text = request.form.get('text', '').strip()

        if input_text:
            try:
                start_time = time.time()
                data = {"text": input_text}
                # todo 调用api函数
                result = predict_fun(data)
                end_time = time.time()
                response_time = round((end_time - start_time) * 1000, 2)
            except Exception as e:
                result = {"error": f"预测失败: {str(e)}"}
                end_time = time.time()
                response_time = round((end_time - start_time) * 1000, 2)

    html_template = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NLP Classifier // 新闻文本分类系统</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400;600&display=swap');
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            :root {
                --bg-primary: #0a0e27;
                --bg-secondary: #15193d;
                --accent-cyan: #00f5ff;
                --accent-purple: #b829dd;
                --accent-green: #00ff88;
                --accent-orange: #ff9500;
                --text-primary: #e0e6ed;
                --text-secondary: #8892b0;
                --border-color: #233554;
                --glow-cyan: 0 0 20px rgba(0, 245, 255, 0.5);
                --glow-purple: 0 0 20px rgba(184, 41, 221, 0.5);
            }
            
            body {
                font-family: 'Fira Code', 'Courier New', monospace;
                background: var(--bg-primary);
                min-height: 100vh;
                position: relative;
                overflow-x: hidden;
                color: var(--text-primary);
            }
            
            body::before {
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: 
                    repeating-linear-gradient(
                        0deg,
                        transparent,
                        transparent 2px,
                        rgba(0, 245, 255, 0.03) 2px,
                        rgba(0, 245, 255, 0.03) 4px
                    );
                pointer-events: none;
                z-index: 1;
            }
            
            .matrix-bg {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: radial-gradient(circle at 50% 50%, rgba(184, 41, 221, 0.1), transparent 70%);
                animation: pulse 8s ease-in-out infinite;
                z-index: 0;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 0.5; transform: scale(1); }
                50% { opacity: 0.8; transform: scale(1.1); }
            }
            
            .container {
                position: relative;
                z-index: 2;
                max-width: 1200px;
                margin: 0 auto;
                padding: 40px 20px;
                padding-bottom: 80px;
            }
            
            .header {
                text-align: center;
                margin-bottom: 50px;
                padding: 30px;
                background: var(--bg-secondary);
                border: 2px solid var(--border-color);
                border-radius: 10px;
                box-shadow: var(--glow-cyan);
                position: relative;
                overflow: hidden;
            }
            
            .header::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 2px;
                background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
                animation: scan 3s linear infinite;
            }
            
            @keyframes scan {
                0% { left: -100%; }
                100% { left: 100%; }
            }
            
            h1 {
                font-size: 36px;
                font-weight: 600;
                background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 10px;
                letter-spacing: 2px;
            }
            
            .subtitle {
                color: var(--text-secondary);
                font-size: 14px;
                margin-top: 10px;
            }
            
            .terminal-window {
                background: var(--bg-secondary);
                border: 2px solid var(--border-color);
                border-radius: 10px;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
                position: relative;
            }
            
            .terminal-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 1px solid var(--border-color);
            }
            
            .terminal-dots {
                display: flex;
                gap: 8px;
            }
            
            .dot {
                width: 12px;
                height: 12px;
                border-radius: 50%;
            }
            
            .dot-red { background: #ff5f56; }
            .dot-yellow { background: #ffbd2e; }
            .dot-green { background: #27c93f; }
            
            .terminal-title {
                flex: 1;
                text-align: center;
                color: var(--text-secondary);
                font-size: 12px;
            }
            
            .input-section {
                margin-bottom: 25px;
            }
            
            .prompt {
                color: var(--accent-green);
                font-size: 16px;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .prompt::before {
                content: '>';
                color: var(--accent-cyan);
                font-weight: bold;
            }
            
            textarea {
                width: 100%;
                min-height: 150px;
                padding: 20px;
                background: rgba(10, 14, 39, 0.8);
                border: 2px solid var(--border-color);
                border-radius: 8px;
                color: var(--accent-cyan);
                font-family: 'Fira Code', monospace;
                font-size: 14px;
                line-height: 1.6;
                resize: vertical;
                transition: all 0.3s;
            }
            
            textarea:focus {
                outline: none;
                border-color: var(--accent-cyan);
                box-shadow: var(--glow-cyan);
            }
            
            textarea::placeholder {
                color: var(--text-secondary);
                opacity: 0.5;
            }
            
            .button-group {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-top: 20px;
            }
            
            .btn-execute {
                padding: 18px;
                background: linear-gradient(135deg, var(--accent-purple), var(--accent-cyan));
                border: none;
                border-radius: 8px;
                color: var(--bg-primary);
                font-family: 'Fira Code', monospace;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                position: relative;
                overflow: hidden;
                transition: all 0.3s;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            
            .btn-execute:hover {
                transform: translateY(-2px);
                box-shadow: var(--glow-purple);
            }
            
            .btn-execute:active {
                transform: translateY(0);
            }
            
            .btn-execute::before {
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                width: 0;
                height: 0;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.3);
                transform: translate(-50%, -50%);
                transition: width 0.6s, height 0.6s;
            }
            
            .btn-execute:hover::before {
                width: 300px;
                height: 300px;
            }
            
            .btn-clear {
                padding: 18px;
                background: transparent;
                border: 2px solid var(--accent-orange);
                border-radius: 8px;
                color: var(--accent-orange);
                font-family: 'Fira Code', monospace;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            
            .btn-clear:hover {
                background: var(--accent-orange);
                color: var(--bg-primary);
                box-shadow: 0 0 20px rgba(255, 149, 0, 0.5);
                transform: translateY(-2px);
            }
            
            .btn-clear:active {
                transform: translateY(0);
            }
            
            .output-section {
                margin-top: 30px;
                animation: fadeIn 0.5s ease-in;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .output-header {
                color: var(--accent-green);
                font-size: 18px;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .output-header::before {
                content: '✓';
                color: var(--accent-cyan);
                font-weight: bold;
                font-size: 20px;
            }
            
            .result-card {
                background: rgba(10, 14, 39, 0.6);
                border: 2px solid var(--accent-cyan);
                border-radius: 8px;
                padding: 25px;
                margin-bottom: 20px;
                position: relative;
                overflow: hidden;
            }
            
            .result-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 4px;
                height: 100%;
                background: linear-gradient(180deg, var(--accent-cyan), var(--accent-purple));
            }
            
            .result-row {
                display: flex;
                margin-bottom: 15px;
                padding: 10px;
                background: rgba(21, 25, 61, 0.5);
                border-radius: 5px;
            }
            
            .result-label {
                color: var(--accent-orange);
                font-weight: 600;
                min-width: 150px;
                flex-shrink: 0;
            }
            
            .result-label::after {
                content: ':';
                margin-left: 5px;
            }
            
            .result-value {
                color: var(--text-primary);
                flex: 1;
                word-break: break-word;
            }
            
            .classification-result {
                color: var(--accent-green);
                font-size: 24px;
                font-weight: 600;
                text-shadow: var(--glow-cyan);
                animation: glow 2s ease-in-out infinite alternate;
            }
            
            @keyframes glow {
                from { text-shadow: 0 0 10px var(--accent-cyan); }
                to { text-shadow: 0 0 20px var(--accent-cyan), 0 0 30px var(--accent-cyan); }
            }
            
            .time-badge {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 8px 15px;
                background: rgba(0, 245, 255, 0.1);
                border: 1px solid var(--accent-cyan);
                border-radius: 20px;
                color: var(--accent-cyan);
                font-size: 14px;
                margin-top: 15px;
            }
            
            .time-badge::before {
                content: '⏱';
                font-size: 16px;
            }
            
            .error-card {
                border-color: #ff6b6b;
            }
            
            .error-card::before {
                background: linear-gradient(180deg, #ff6b6b, #ff9500);
            }
            
            .error-header::before {
                content: '✗';
                color: #ff6b6b;
            }
            
            .error-message {
                color: #ff6b6b;
                font-size: 16px;
            }
            
            .cursor-blink {
                display: inline-block;
                width: 10px;
                height: 18px;
                background: var(--accent-cyan);
                animation: blink 1s step-end infinite;
                vertical-align: middle;
                margin-left: 5px;
            }
            
            @keyframes blink {
                50% { opacity: 0; }
            }
            
            .status-bar {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                background: var(--bg-secondary);
                border-top: 2px solid var(--border-color);
                padding: 10px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 12px;
                color: var(--text-secondary);
                z-index: 100;
            }
            
            .status-item {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .status-indicator {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: var(--accent-green);
                animation: statusPulse 2s ease-in-out infinite;
            }
            
            @keyframes statusPulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.3; }
            }
            
            ::-webkit-scrollbar {
                width: 10px;
                height: 10px;
            }
            
            ::-webkit-scrollbar-track {
                background: var(--bg-primary);
            }
            
            ::-webkit-scrollbar-thumb {
                background: var(--border-color);
                border-radius: 5px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: var(--accent-cyan);
            }
        </style>
    </head>
    <body>
        <div class="matrix-bg"></div>
        
        <div class="container">
            <div class="header">
                <h1>⚡ NLP_TEXT_CLASSIFIER v1.0</h1>
                <div class="subtitle">// 基于随机森林的新闻文本智能分类系统</div>
            </div>
            
            <div class="terminal-window">
                <div class="terminal-header">
                    <div class="terminal-dots">
                        <div class="dot dot-red"></div>
                        <div class="dot dot-yellow"></div>
                        <div class="dot dot-green"></div>
                    </div>
                    <div class="terminal-title">classifier_input.py</div>
                    <div style="width: 60px;"></div>
                </div>
                
                <form method="POST" action="/" id="classifyForm">
                    <div class="input-section">
                        <div class="prompt">请输入待分类的新闻文本<span class="cursor-blink"></span></div>
                        <textarea 
                            id="text" 
                            name="text" 
                            placeholder="// 在此输入新闻内容...&#10;// 系统将自动分析并返回分类结果"
                            required>{{ input_text }}</textarea>
                    </div>
                    
                    <div class="button-group">
                        <button type="submit" class="btn-execute">
                            ▶ EXECUTE_CLASSIFICATION
                        </button>
                        <button type="button" class="btn-clear" onclick="clearText()">
                            ⟲ CLEAR_INPUT
                        </button>
                    </div>
                </form>
            </div>
            
            {% if result %}
                {% if 'error' in result %}
                    <div class="output-section">
                        <div class="output-header error-header">ERROR DETECTED</div>
                        <div class="result-card error-card">
                            <div class="result-row">
                                <div class="result-label" style="color: #ff6b6b;">Error_Type</div>
                                <div class="result-value error-message">{{ result.error }}</div>
                            </div>
                            {% if response_time %}
                            <div class="time-badge">
                                Response Time: {{ response_time }} ms
                            </div>
                            {% endif %}
                        </div>
                    </div>
                {% else %}
                    <div class="output-section">
                        <div class="output-header">CLASSIFICATION_COMPLETE</div>
                        <div class="result-card">
                            <div class="result-row">
                                <div class="result-label">Input_Text</div>
                                <div class="result-value">{{ result.text[:300] }}{% if result.text|length > 300 %}...{% endif %}</div>
                            </div>
                            <div class="result-row">
                                <div class="result-label">Prediction</div>
                                <div class="result-value classification-result">{{ result.predict_class }}</div>
                            </div>
                            {% if response_time %}
                            <div class="time-badge">
                                Response Time: {{ response_time }} ms
                            </div>
                            {% endif %}
                        </div>
                    </div>
                {% endif %}
            {% endif %}
        </div>
        
        <div class="status-bar">
            <div class="status-item">
                <div class="status-indicator"></div>
                <span>SYSTEM ONLINE</span>
            </div>
            <div class="status-item">
                <span>MODEL: RANDOM_FOREST | STATUS: READY</span>
            </div>
            <div class="status-item">
                <span>PORT: 9091</span>
            </div>
        </div>
        
        <script>
            function clearText() {
                document.getElementById('text').value = '';
                document.getElementById('text').focus();
            }
        </script>
    </body>
    </html>
    """

    return render_template_string(html_template, result=result, input_text=input_text, response_time=response_time)


if __name__ == '__main__':
    print("=" * 50)
    print("🚀 新闻文本分类系统启动中...")
    print("=" * 50)
    print("📍 访问地址: http://127.0.0.1:9091")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=9091)
