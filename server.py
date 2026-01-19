from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import subprocess
from dotenv import load_dotenv, set_key, dotenv_values

app = Flask(__name__, static_folder='static')

ENV_FILE = '.env'

@app.route('/')
def index():
    """主页面"""
    return send_from_directory('static', 'index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取当前配置"""
    # 强制重新加载 .env 文件，覆盖内存中的旧环境变量
    load_dotenv(override=True)
    config = {
        'SCOUT_MIN_VOLUME': os.getenv('SCOUT_MIN_VOLUME', '5000'),
        'SCOUT_MIN_PROB': os.getenv('SCOUT_MIN_PROB', '0.15'),
        'SCOUT_MAX_PROB': os.getenv('SCOUT_MAX_PROB', '0.85'),
        'SCOUT_TAG': os.getenv('SCOUT_TAG', ''),
        'SCOUT_MIN_LIQUIDITY': os.getenv('SCOUT_MIN_LIQUIDITY', ''),
        'SCOUT_MAX_DAYS_TO_END': os.getenv('SCOUT_MAX_DAYS_TO_END', ''),
        'SCOUT_SEARCH': os.getenv('SCOUT_SEARCH', ''),
        'SCOUT_EXCLUDE_KEYWORDS': os.getenv('SCOUT_EXCLUDE_KEYWORDS', ''),
        'SCOUT_ORDER_BY': os.getenv('SCOUT_ORDER_BY', 'volume'),
        'SCOUT_FETCH_LIMIT': os.getenv('SCOUT_FETCH_LIMIT', '200'),
        'SCOUT_RUNTIME_LIMIT': os.getenv('SCOUT_RUNTIME_LIMIT', '30'),
        'SCOUT_WEBHOOK_URL': os.getenv('SCOUT_WEBHOOK_URL', ''),
        'SCOUT_AUTO_PRESET': os.getenv('SCOUT_AUTO_PRESET', ''),
    }
    return jsonify(config)

@app.route('/api/config', methods=['POST'])
def save_config():
    """保存配置到 .env 文件"""
    try:
        config = request.json
        
        # 更新 .env 文件并同步到内存环境变量
        for key, value in config.items():
            str_val = str(value)
            set_key(ENV_FILE, key, str_val)
            os.environ[key] = str_val
        
        return jsonify({'success': True, 'message': '配置已保存'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500

@app.route('/api/scout', methods=['POST'])
def run_scout():
    """运行侦察脚本"""
    try:
        # [核心修复] 运行前先删除旧的结果文件
        if os.path.exists('markets_list.txt'):
            try:
                os.remove('markets_list.txt')
            except Exception as e:
                print(f"⚠️ 无法删除旧文件: {e}")

        # 1. 准备基础环境
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'

        # 2. 从请求中获取临时配置 (Stateless)
        # 如果前端传了 config，直接用来覆盖环境变量，不再依赖 global state
        params = request.json or {}
        if params:
            print("🔧 [Server] 接收到临时作战指令，正在覆盖环境变量...")
            for key, value in params.items():
                env[key] = str(value)
                # 打印一下看看收到了什么 (Debug)
                if key in ['SCOUT_TAG', 'SCOUT_SEARCH', 'SCOUT_MIN_VOLUME']:
                    print(f"  -> {key}: {value}")

        # 运行 scout.py 并捕获输出
        result = subprocess.run(
            ['python', 'scout.py'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60,
            env=env
        )
        
        # 读取生成的 markets_list.txt
        markets_data = ""
        if os.path.exists('markets_list.txt'):
            with open('markets_list.txt', 'r', encoding='utf-8') as f:
                markets_data = f.read()
                
            # [Debug Fix] 如果文件中显示 0 条记录，强制追加 stdout 中的调试日志
            if "共计收录: 0 条记录" in markets_data:
                 safe_output = (result.stdout or "") + "\n" + (result.stderr or "")
                 markets_data += f"\n\n=== 🕵️‍♂️ 调试日志 (DEBUG LOGS) ===\n{safe_output}"
        else:
            # 如果文件不存在，说明脚本运行失败或没拿到数据
            if result.returncode != 0:
                # 安全获取 output
                err_msg = result.stderr or "未知错误"
                markets_data = f"❌ 脚本执行出错:\n{err_msg}"
            else:
                 # [Debug Fix] 如果没有结果，直接返回终端输出(stdout)，方便看到调试信息
                 markets_data = f"⚠️ 未找到符合条件的市场 (Volume > {os.getenv('SCOUT_MIN_VOLUME', '?')})\n\n[终端调试日志]\n{safe_output}"
        
        # 安全拼接 output
        safe_output = (result.stdout or "") + "\n" + (result.stderr or "")
        
        return jsonify({
            'success': True,
            'output': safe_output,
            'markets': markets_data
        })
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'message': '侦察超时'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'执行失败: {str(e)}'}), 500


# 简单的内存缓存
TAGS_CACHE = {
    'data': [],
    'timestamp': 0
}
CACHE_DURATION = 3600  # 缓存 1 小时

@app.route('/api/tags', methods=['GET'])
def get_tags():
    """获取所有可用的品类标签 (带缓存)"""
    global TAGS_CACHE
    import time
    
    current_time = time.time()
    
    # 检查缓存是否有效
    if TAGS_CACHE['data'] and (current_time - TAGS_CACHE['timestamp'] < CACHE_DURATION):
        return jsonify(TAGS_CACHE['data'])

    try:
        import requests
        # 增加超时时间，避免网络波动
        response = requests.get('https://gamma-api.polymarket.com/tags?limit=5000', timeout=15)
        response.raise_for_status() # 检查 HTTP 错误
        tags = response.json()
        
        # 过滤和排序标签
        filtered_tags = [
            {'id': t.get('id'), 'label': t.get('label')}
            for t in tags
            if t.get('label') and len(t.get('label', '')) < 30
        ]
        
        # 定义优先展示的热门标签
        PRIORITY_TAGS = ['Politics', 'Crypto', 'Sports', 'Business', 'Science', 'Pop Culture', 'News', 'Middle East', 'USA']
        
        # 1. 分离出热门标签
        priority_list = []
        others_list = []
        
        for t in filtered_tags:
            if t['label'] in PRIORITY_TAGS:
                priority_list.append(t)
            else:
                others_list.append(t)
                
        # 2. 热门标签按预定义顺序排序
        priority_list.sort(key=lambda x: PRIORITY_TAGS.index(x['label']) if x['label'] in PRIORITY_TAGS else 999)
        
        # 3. 其他标签按字母排序
        others_list.sort(key=lambda x: str(x['label']).lower())
        
        # 合并
        final_tags = priority_list + others_list
        
        # 更新缓存
        TAGS_CACHE['data'] = final_tags
        TAGS_CACHE['timestamp'] = current_time
        
        return jsonify(final_tags)
    except Exception as e:
        print(f"❌ 获取标签失败: {e}")
        # 如果有旧缓存，即使过期也返回，比报错好
        if TAGS_CACHE['data']:
            print("⚠️ 使用过期缓存")
            return jsonify(TAGS_CACHE['data'])
            
        # 最后的手段：返回空列表，避免前端崩坏
        return jsonify([])

@app.route('/api/presets', methods=['GET'])
def get_presets():
    """获取所有预设方案"""
    try:
        if not os.path.exists('presets'):
            os.makedirs('presets')
        
        presets = []
        for f in os.listdir('presets'):
            if f.endswith('.json'):
                presets.append(f.replace('.json', ''))
        return jsonify(presets)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/presets/<name>', methods=['GET'])
def load_preset(name):
    """加载指定预设方案"""
    try:
        import json
        file_path = f'presets/{name}.json'
        if not os.path.exists(file_path):
            return jsonify({'error': '方案不存在'}), 404
            
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/presets', methods=['POST'])
def save_preset():
    """保存预设方案"""
    try:
        import json
        data = request.json
        name = data.get('name')
        config = data.get('config')
        
        if not name or not config:
            return jsonify({'success': False, 'message': '参数不完整'}), 400
            
        if not os.path.exists('presets'):
            os.makedirs('presets')
            
        with open(f'presets/{name}.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            
        return jsonify({'success': True, 'message': '方案已保存'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500

@app.route('/api/test_webhook', methods=['POST'])
def test_webhook():
    data = request.json or {}
    url = data.get('url')
    if not url:
        return jsonify({"success": False, "message": "URL不能为空"})
    
    try:
        # 发送测试消息
        payload = {
            "content": "🔔 **Mikon AI Scout 通信测试**\n\n收到这条消息意味着 Webhook 配置成功！\nReady to dispatch intel.",
            "username": "Mikon Scout Bot"
        }
        resp = requests.post(url, json=payload, timeout=5)
        if resp.status_code in [200, 201, 204]:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": f"HTTP {resp.status_code}: {resp.text}"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

if __name__ == '__main__':
    print("🎯 Polymarket Scout Web 界面启动中...")
    print("📡 访问地址: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
