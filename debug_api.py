import json
from py_clob_client.client import ClobClient

CLOB_ENDPOINT = "https://clob.polymarket.com"

def debug():
    client = ClobClient(CLOB_ENDPOINT)
    print("正在获取市场数据...")
    resp = client.get_markets()
    
    with open("api_dump.json", "w", encoding="utf-8") as f:
        json.dump(resp, f, indent=2, ensure_ascii=False)
    
    print("API 原始数据已保存至 api_dump.json")
    
    if isinstance(resp, dict) and 'data' in resp:
        markets = resp['data']
    else:
        markets = resp
        
    if markets and len(markets) > 0:
        print(f"抓取到 {len(markets)} 个市场。")
        print("第一个市场的结构示例:")
        print(json.dumps(markets[0], indent=2, ensure_ascii=False))
    else:
        print("未抓取到任何市场数据。")

if __name__ == "__main__":
    debug()
