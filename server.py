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
    load_dotenv()
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
    }
    return jsonify(config)

@app.route('/api/config', methods=['POST'])
def save_config():
    """保存配置到 .env 文件"""
    try:
        config = request.json
        
        # 更新 .env 文件
        for key, value in config.items():
            set_key(ENV_FILE, key, str(value))
        
        return jsonify({'success': True, 'message': '配置已保存'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500

@app.route('/api/scout', methods=['POST'])
def run_scout():
    """运行侦察脚本"""
    try:
        # 运行 scout.py 并捕获输出
        result = subprocess.run(
            ['python', 'scout.py'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60
        )
        
        # 读取生成的 markets_list.txt
        markets_data = ""
        if os.path.exists('markets_list.txt'):
            with open('markets_list.txt', 'r', encoding='utf-8') as f:
                markets_data = f.read()
        
        return jsonify({
            'success': True,
            'output': result.stdout,
            'markets': markets_data
        })
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'message': '侦察超时'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'执行失败: {str(e)}'}), 500

@app.route('/api/tags', methods=['GET'])
def get_tags():
    """获取所有可用的品类标签"""
    try:
        import requests
        response = requests.get('https://gamma-api.polymarket.com/tags?limit=5000', timeout=10)
        tags = response.json()
        
        # 过滤和排序标签
        filtered_tags = [
            {'id': t.get('id'), 'label': t.get('label')}
            for t in tags
            if t.get('label') and len(t.get('label', '')) < 30
        ]
        
        # 按字母排序
        filtered_tags.sort(key=lambda x: x['label'].lower())
        
        return jsonify(filtered_tags)
    except Exception as e:
        return jsonify(filtered_tags)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

if __name__ == '__main__':
    print("🎯 Polymarket Scout Web 界面启动中...")
    print("📡 访问地址: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
