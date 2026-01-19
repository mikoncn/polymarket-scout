import sys
import requests
import pandas as pd
import time
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# 加载配置
load_dotenv()

# 处理 Windows 系统中的 UTF-8 编码问题
# 移除手动重定向，交给 rich 处理


console = Console()

# 配置载入 (带默认值回退)
MIN_VOLUME = float(os.getenv("SCOUT_MIN_VOLUME", 5000))
MIN_PROB = float(os.getenv("SCOUT_MIN_PROB", 0.15))
MAX_PROB = float(os.getenv("SCOUT_MAX_PROB", 0.85))
FETCH_LIMIT = int(os.getenv("SCOUT_FETCH_LIMIT", 200))
MAX_RUNTIME = int(os.getenv("SCOUT_RUNTIME_LIMIT", 30))
SCOUT_TAG_NAME = os.getenv("SCOUT_TAG", "").strip()

# 高级可选配置 (全部带默认值)
MIN_LIQUIDITY = float(os.getenv("SCOUT_MIN_LIQUIDITY", 0) or 0)
MAX_DAYS_TO_END = int(os.getenv("SCOUT_MAX_DAYS_TO_END", 0) or 0)
SEARCH_KEYWORD = os.getenv("SCOUT_SEARCH", "").strip()
EXCLUDE_KEYWORDS = [k.strip().lower() for k in os.getenv("SCOUT_EXCLUDE_KEYWORDS", "").split(',') if k.strip()]
ORDER_BY = os.getenv("SCOUT_ORDER_BY", "volume").strip().lower()

def get_tag_id(tag_name):
    """根据品类名称智能匹配 Tag ID"""
    if not tag_name:
        return None, None
    try:
        # 尝试搜索匹配的标签 (扩大搜索范围并优先精确匹配)
        url = f"https://gamma-api.polymarket.com/tags?limit=1000"
        resp = requests.get(url, timeout=5)
        tags = resp.json()
        
        # 第一轮：寻找精确匹配
        for t in tags:
            label = t.get('label', '')
            if tag_name.lower() == label.lower():
                return t.get('id'), t.get('label')
        
        # 第二轮：模糊匹配
        for t in tags:
            label = t.get('label', '').lower()
            if tag_name.lower() in label:
                return t.get('id'), t.get('label')
    except:
        pass
    return None, None

def scout():
    start_t = time.time()
    console.print(f"\n[bold cyan][Mikon AI Army][/bold cyan] 闪电侦察启动 ({MAX_RUNTIME}s 倒计时)...")
    
    tag_id, actual_label = get_tag_id(SCOUT_TAG_NAME)
    if SCOUT_TAG_NAME and not tag_id:
        console.print(f"[yellow]⚠️ 未找到品类 '{SCOUT_TAG_NAME}'，将执行全局扫描。[/yellow]")
        tag_info = " | 品类: 全局"
    elif tag_id:
        tag_info = f" | 品类: {actual_label} (ID: {tag_id})"
    else:
        tag_info = " | 品类: 全局"
        
    console.print(f"[dim]当前配置规则: 成交量 > ${MIN_VOLUME:,.0f} | 胜率 {MIN_PROB:.0%} - {MAX_PROB:.0%}{tag_info}[/dim]\n")
    
    final_data = []
    with console.status("[bold green]正在突袭 Polymarket 数据中心...", spinner="earth"):
        try:
            # 1. 尝试从 Gamma API 获取活跃市场
            tag_param = f"&tag_id={tag_id}" if tag_id else ""
            url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit={FETCH_LIMIT}{tag_param}"
            resp = requests.get(url, timeout=10)
            markets = resp.json()
            
            # API 结构校验与容错
            if not isinstance(markets, list):
                if isinstance(markets, dict) and 'data' in markets:
                    markets = markets['data']
                else:
                    markets = []

            for m in markets:
                # 30秒硬限制保护
                if time.time() - start_t > MAX_RUNTIME - 4:
                    break
                    
                title = m.get('question', m.get('title', '未知市场'))
                vol = float(m.get('volume', 0))
                slug = m.get('market_slug', m.get('slug', ''))
                
                # 构造连接 (使用 /market/ 前缀以确保自动重定向，避免 /event/ 导致的 404)
                link = f"https://polymarket.com/market/{slug}" if slug else "N/A"
                
                if m.get('closed') is True or m.get('resolved') is True:
                    continue

                # 价格信息探针
                prices = m.get('outcomePrices', [])
                if isinstance(prices, str):
                    try:
                        import json
                        prices = json.loads(prices)
                    except:
                        prices = []
                
                if not prices:
                    prices = [t.get('price') for t in m.get('tokens', []) if t.get('price') is not None]
                
                if not prices:
                    continue
                
                prob = float(prices[0]) if prices[0] is not None else 0.5
                
                # 过滤极其接近结盘的市场 (胜率 > 99% 或 < 1% 视为无效)
                if prob > 0.99 or prob < 0.01:
                    continue
                
                # 提取流动性和结束日期
                liquidity = float(m.get('liquidity', 0))
                end_date_str = m.get('endDate', '')
                
                # 高级过滤条件 (可选)
                # 1. 流动性过滤
                if MIN_LIQUIDITY > 0 and liquidity < MIN_LIQUIDITY:
                    continue
                
                # 2. 结束日期倒计时过滤
                days_to_end = None
                if MAX_DAYS_TO_END > 0 and end_date_str:
                    try:
                        from datetime import datetime
                        end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                        days_to_end = (end_date - datetime.now(end_date.tzinfo)).days
                        if days_to_end < 0 or days_to_end > MAX_DAYS_TO_END:
                            continue
                    except:
                        pass
                
                # 3. 关键词搜索过滤
                if SEARCH_KEYWORD and SEARCH_KEYWORD.lower() not in str(title).lower():
                    continue
                
                # 4. 排除关键词黑名单
                if EXCLUDE_KEYWORDS:
                    is_excluded = False
                    for kw in EXCLUDE_KEYWORDS:
                        if kw in str(title).lower():
                            is_excluded = True
                            break
                    if is_excluded:
                        continue

                final_data.append({
                    "Title": str(title),
                    "Volume": vol,
                    "Prob": prob,
                    "Liquidity": liquidity,
                    "DaysToEnd": days_to_end,
                    "Link": link
                })
        except Exception as e:
            console.print(f"[dim red]探测异常: {e}[/dim red]")
            pass

    # 兜底：如果 API 暂时不可用，载入模拟侦查数据
    if not final_data:
        console.print("[yellow]警告: 实时 API 探测超时或受限。正在载入模拟侦查数据进行演示...[/yellow]")
        final_data = [
            {"Title": "Will Bitcoin reach $150k in 2025?", "Volume": 2520485, "Prob": 0.42, "Liquidity": 125000, "DaysToEnd": 45, "Link": "https://polymarket.com/market/bitcoin-reach-150k-in-2025"},
            {"Title": "Will GPT-5 be announced by OpenAI this year?", "Volume": 1890420, "Prob": 0.65, "Liquidity": 98000, "DaysToEnd": 120, "Link": "https://polymarket.com/market/gpt-5-announcement-2025"},
            {"Title": "Federal Reserve to cut rates in March 2025?", "Volume": 950200, "Prob": 0.58, "Liquidity": 67000, "DaysToEnd": 15, "Link": "https://polymarket.com/market/fed-rate-cut-march-2025"},
            {"Title": "SpaceX Starship reaches orbit on next flight?", "Volume": 420500, "Prob": 0.78, "Liquidity": 45000, "DaysToEnd": 7, "Link": "https://polymarket.com/market/starship-flight-next-success"},
            {"Title": "Nvidia Stock to hit $200 by end of Q2?", "Volume": 356000, "Prob": 0.31, "Liquidity": 32000, "DaysToEnd": 90, "Link": "https://polymarket.com/market/nvda-stock-200-q2"},
            {"Title": "Sample Small Inactive Market (Filtered)", "Volume": 1200, "Prob": 0.50, "Liquidity": 500, "DaysToEnd": None, "Link": "N/A"}
        ]

    # 按配置的排序策略排序
    sort_key_map = {
        'volume': lambda x: x['Volume'],
        'liquidity': lambda x: x.get('Liquidity', 0),
        'enddate': lambda x: x.get('DaysToEnd', 999999) if x.get('DaysToEnd') is not None else 999999,
        'prob': lambda x: abs(x['Prob'] - 0.5)  # 极端值优先
    }
    
    sort_key = sort_key_map.get(ORDER_BY, sort_key_map['volume'])
    sorted_data = sorted(final_data, key=sort_key, reverse=True)
    
    # 应用 Vibe Filter (自定义或默认胜率区间)
    vibe_list = [r for r in sorted_data if r['Volume'] > MIN_VOLUME and MIN_PROB <= r['Prob'] <= MAX_PROB]
    
    display_list = []
    header = ""
    if vibe_list:
        # 放宽展示数量到前 50 条
        display_list = vibe_list[:50]
        header = f"💎 核心侦察结果 (查获 {len(vibe_list)} 个优质市场)"
    else:
        display_list = sorted_data[:20]
        header = "📡 全局快照 (仅展示高成交量)"
        console.print(f"[dim]提示：目前无市场符合 {MIN_PROB:.0%}-{MAX_PROB:.0%} 胜率规则，已输出当前成交量最高的数据。[/dim]")

    # 绘制 Rich 表格
    table = Table(title=f"{header}", border_style="cyan", header_style="bold magenta")
    table.add_column("侦察目标 (Market)", style="white")
    table.add_column("胜率", justify="center", style="green")
    table.add_column("成交量", justify="right", style="blue")
    table.add_column("查看链接 (Link)", justify="left", style="underline cyan")

    for r in display_list:
        table.add_row(
            r['Title'][:60],
            f"{r['Prob']:.1%}",
            f"${r['Volume']:,.0f}",
            r['Link']
        )

    console.print(table)
    
    # 持久化存储
    try:
        with open("markets_list.txt", "w", encoding="utf-8") as f:
            f.write(f"=== Mikon AI Scout 侦察完整名单 ({pd.Timestamp.now()}) ===\n")
            f.write(f"共计收录: {len(display_list)} 条记录\n\n")
            for i, r in enumerate(display_list, 1):
                f.write(f"{i}. 【{r['Prob']:.1%}】{r['Title']}\n")
                f.write(f"   成交量: ${r['Volume']:,.0f}\n")
                f.write(f"   查看链接: {r['Link']}\n")
                f.write("-" * 50 + "\n")
        console.print(f"\n[bold green]💾 完整名单（含链接）已存至: markets_list.txt[/bold green]")
    except Exception as e:
        console.print(f"[red]保存失败: {e}[/red]")

    console.print(f"\n[bold green]✅ 侦察任务完成。总耗时: {time.time()-start_t:.1f}s[/bold green]")

if __name__ == "__main__":
    scout()
