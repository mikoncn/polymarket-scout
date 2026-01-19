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

# 配置载入 (主要从 .env 加载，如果存在 SCOUT_AUTO_PRESET 则从预设 JSON 覆盖)
MIN_VOLUME = float(os.getenv("SCOUT_MIN_VOLUME", 5000))
MIN_PROB = float(os.getenv("SCOUT_MIN_PROB", 0.15))
MAX_PROB = float(os.getenv("SCOUT_MAX_PROB", 0.85))
FETCH_LIMIT = int(os.getenv("SCOUT_FETCH_LIMIT", 200))
MAX_RUNTIME = int(os.getenv("SCOUT_RUNTIME_LIMIT", 30))
SCOUT_TAG_NAME = os.getenv("SCOUT_TAG", "").strip()
MIN_LIQUIDITY = float(os.getenv("SCOUT_MIN_LIQUIDITY", 0) or 0)
MAX_DAYS_TO_END = int(os.getenv("SCOUT_MAX_DAYS_TO_END", -1) or -1)
SEARCH_KEYWORD = os.getenv("SCOUT_SEARCH", "").strip()
EXCLUDE_KEYWORDS_RAW = os.getenv("SCOUT_EXCLUDE_KEYWORDS", "")
ORDER_BY = os.getenv("SCOUT_ORDER_BY", "volume").strip().lower()

# [Automation] 默认任务预设覆盖逻辑
AUTO_PRESET = os.getenv("SCOUT_AUTO_PRESET", "").strip().replace("'", "").replace('"', '')
if AUTO_PRESET:
    import json
    preset_path = os.path.join("presets", f"{AUTO_PRESET}.json")
    if os.path.exists(preset_path):
        console.print(f"[bold cyan][Mikon AI][/bold cyan] 🤖 自动化模式启动: [yellow]{AUTO_PRESET}[/yellow]")
        try:
            with open(preset_path, 'r', encoding='utf-8') as f:
                preset_data = json.load(f)
                if "SCOUT_MIN_VOLUME" in preset_data: MIN_VOLUME = float(preset_data["SCOUT_MIN_VOLUME"] or 0)
                if "SCOUT_MIN_PROB" in preset_data: MIN_PROB = float(preset_data["SCOUT_MIN_PROB"] or 0)
                if "SCOUT_MAX_PROB" in preset_data: MAX_PROB = float(preset_data["SCOUT_MAX_PROB"] or 1)
                if "SCOUT_TAG" in preset_data: SCOUT_TAG_NAME = str(preset_data["SCOUT_TAG"] or "").strip()
                if "SCOUT_MIN_LIQUIDITY" in preset_data: MIN_LIQUIDITY = float(preset_data["SCOUT_MIN_LIQUIDITY"] or 0)
                if "SCOUT_MAX_DAYS_TO_END" in preset_data: MAX_DAYS_TO_END = int(preset_data.get("SCOUT_MAX_DAYS_TO_END") or -1)
                if "SCOUT_SEARCH" in preset_data: SEARCH_KEYWORD = str(preset_data["SCOUT_SEARCH"] or "").strip()
                if "SCOUT_EXCLUDE_KEYWORDS" in preset_data: EXCLUDE_KEYWORDS_RAW = str(preset_data["SCOUT_EXCLUDE_KEYWORDS"] or "")
                if "SCOUT_ORDER_BY" in preset_data: ORDER_BY = str(preset_data["SCOUT_ORDER_BY"] or "volume").strip().lower()
                if "SCOUT_FETCH_LIMIT" in preset_data: FETCH_LIMIT = int(preset_data["SCOUT_FETCH_LIMIT"] or 200)
                if "SCOUT_RUNTIME_LIMIT" in preset_data: MAX_RUNTIME = int(preset_data["SCOUT_RUNTIME_LIMIT"] or 30)
                console.print(f"[green]✅ 已同步 [bold]{AUTO_PRESET}[/bold] 的所有作战指令。[/green]\n")
        except Exception as e:
            console.print(f"[red]❌ 预设加载失败: {e}[/red]")

# 后处理
EXCLUDE_KEYWORDS = [k.strip().lower() for k in EXCLUDE_KEYWORDS_RAW.split(',') if k.strip()]

def get_tag_id(tag_name):
    """根据品类名称智能匹配 Tag ID"""
    if not tag_name:
        return None, None
        
    # [Feature] 如果输入的是纯数字，直接当做 ID 使用
    if str(tag_name).isdigit():
        return str(tag_name), f"Tag-{tag_name}"

    try:
        # 尝试搜索匹配的标签 (扩大搜索范围并优先精确匹配)
        url = f"https://gamma-api.polymarket.com/tags?limit=5000"
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
    tag_info = f" | 品类: {actual_label} (ID: {tag_id})" if tag_id else " | 品类: 全局"
        
    console.print(f"[dim]当前配置规则: 成交量 > ${MIN_VOLUME:,.0f} | 胜率 {MIN_PROB:.0%} - {MAX_PROB:.0%}{tag_info}[/dim]")
    if MAX_DAYS_TO_END >= 0:
        console.print(f"[dim yellow]⏳ 倒计时过滤: 仅显示 {MAX_DAYS_TO_END} 天内结盘的市场[/dim yellow]")
    console.print("")
    
    # 初始化变量
    final_data = []
    error_msg = None

    with console.status("[bold green]正在突袭 Polymarket 数据中心...", spinner="earth"):
        try:
            # 1. 分页获取活跃市场 (绕过单次 500 条限制)
            all_markets = []
            offset = 0
            
            # 读取排序配置
            ORDER_BY = os.getenv("SCOUT_ORDER_BY", "volume")
            
            # 映射排序参数
            sort_param = ""
            if ORDER_BY == "liquidity":
                sort_param = "&order=liquidity&ascending=false"
            elif ORDER_BY == "endDate":
                # 按由于结束日期排序 (即将过期的排前面)
                sort_param = "&order=endDate&ascending=true" 
            else:
                # 默认按 Volume 降序
                sort_param = "&order=volume&ascending=false"

            # 构造基础 URL 参数
            base_params = f"active=true&closed=false{sort_param}"
            tag_param = f"&tag_id={tag_id}" if tag_id else ""
            
            # [核心优化] 使用 Server-Side 过滤结束日期 (如果你想要日结，就只拉取日结的数据!)
            date_filter_param = ""
            if MAX_DAYS_TO_END >= 0:
                # 计算截止日期 (当前时间 + MAX_DAYS)
                # 使用 datetime to ISO format
                import datetime
                # 注意: API 需要 UTC 时间格式 ISO
                future_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=MAX_DAYS_TO_END + 1)
                date_str = future_date.isoformat().replace("+00:00", "Z") # 兼容性调整
                date_filter_param = f"&end_date_max={date_str}"
                console.print(f"[dim cyan]🚀 启用服务端极速过滤: end_date_max={date_str}[/dim cyan]")

            
            # 如果 FETCH_LIMIT 为 1000，需要循环 offset=0, offset=500
            while len(all_markets) < FETCH_LIMIT:
                # 剩余需要获取的数量
                remaining = FETCH_LIMIT - len(all_markets)
                # 单次最大 500 (Gamma API 限制)
                batch_limit = min(500, remaining)
                
                url = f"https://gamma-api.polymarket.com/markets?{base_params}&limit={batch_limit}&offset={offset}{tag_param}{date_filter_param}"
                
                # 增加 User-Agent 伪装和超时时间
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                
                # console.print(f"DEBUG: Fetching offset {offset}...") 
                resp = requests.get(url, headers=headers, timeout=30)
                batch_data = resp.json()
                
                # API 结构校验与容错
                if not isinstance(batch_data, list):
                    if isinstance(batch_data, dict) and 'data' in batch_data:
                        batch_data = batch_data['data']
                    else:
                        batch_data = []
                
                if not batch_data:
                    break # 没有更多数据了
                    
                all_markets.extend(batch_data)
                offset += len(batch_data)
                
                # 避免过快请求
                time.sleep(0.2)
            
            # 使用所有获取到的市场进行过滤
            markets = all_markets
            
            # [URL 去重] 用于记录已处理的链接
            seen_urls = set()

            for m in markets:
                # 30秒硬限制保护 -> 放宽到 60s
                if time.time() - start_t > MAX_RUNTIME:
                     error_msg = f"已达到最大运行时间 ({MAX_RUNTIME}s)，提前返回部分结果"
                     break
                     
                title = m.get('question', m.get('title', 'Unknown'))
                slug = m.get('slug', '') # market slug
                
                # 构造链接用于去重检查
                # API 通常返回 market_slug，链接是 polymarket.com/market/{slug}
                # 或者 event_slug?
                # 为了稳妥，我们用生成的 full_url 去重
                market_slug = m.get('slug', '')
                event_slug = m.get('event_slug', '') # 有些有 event_slug
                
                # 优先使用 event_slug 如果存在 (因为多个 market 可能属于同一个 event)
                # 但用户说 "链接一样"，通常是 event page
                # 我们先生成 url，再 check
                
                # 构建 URL (Gamma API 返回 slug)
                url = f"https://polymarket.com/market/{market_slug}"
                
                # 如果这个 URL 已经出现过，直接跳过 (用户要求: generate one record)
                if url in seen_urls:
                    continue
                
                seen_urls.add(url)
                
                desc = m.get('description', '')
                vol = float(m.get('volume', 0))
                slug = m.get('market_slug', m.get('slug', ''))
                
                # ... (后续处理保持不变)
                # 构造连接
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
                
                # 如果开启了倒计时过滤 (>=0)，则必须有有效的结束日期
                if MAX_DAYS_TO_END >= 0 and not end_date_str:
                    continue

                if end_date_str:
                    try:
                        # 使用 pandas 进行更稳健的日期解析
                        end_date = pd.to_datetime(end_date_str)
                        if end_date.tzinfo is None:
                            end_date = end_date.tz_localize('UTC')
                        
                        now = pd.Timestamp.now(tz='UTC')
                        delta = end_date - now
                        days_to_end = delta.days
                        
                        # Only apply filter if enabled (>=0)
                        if MAX_DAYS_TO_END >= 0:
                            # 严格过滤: 必须在 [0, MAX] 范围内 (负数表示已过期但未结算，通常排除，或需用户指定)
                            # 这里保持 < 0 也排除，因为我们要找未来的. 
                            # 修正: days_to_end=0 means < 24h. 
                            if days_to_end < 0 or days_to_end > MAX_DAYS_TO_END:
                                continue
                    except Exception as e:
                        # 日期解析失败，如果开启了严格过滤，则排除
                        if MAX_DAYS_TO_END >= 0:
                            continue
                        pass
                
                # 3. 关键词搜索过滤 (支持逗号分隔的 OR 逻辑)
                if SEARCH_KEYWORD:
                    keywords = [k.strip().lower() for k in SEARCH_KEYWORD.split(',') if k.strip()]
                    title_lower = str(title).lower()
                    if keywords:
                        match_found = False
                        for kw in keywords:
                            if kw in title_lower:
                                match_found = True
                                break
                        if not match_found:
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
                    "DaysToEnd": days_to_end if days_to_end is not None else 999,
                    "Link": link
                })
        except Exception as e:
            error_msg = str(e)
            console.print(f"[dim red]探测异常: {e}[/dim red]")
            pass

    # 兜底：如果 API 异常导致无数据，显示错误信息
    if not final_data:
        if error_msg:
             console.print(f"[yellow]警告: API 请求失败 ({error_msg})[/yellow]")
             final_data = [{
                "Title": f"⚠️ 错误: API 连接失败 - {error_msg}", 
                "Volume": 0, "Prob": 0.5, "Liquidity": 0, "DaysToEnd": 0, "Link": "N/A"
             }]
        else:
             # 如果没有报错但过滤完了，显示空提示
             final_data = []

    # 按配置的排序策略排序
    sort_key_map = {
        'volume': lambda x: x['Volume'],
        'liquidity': lambda x: x.get('Liquidity', 0),
        'enddate': lambda x: x.get('DaysToEnd', 999999),
        'prob': lambda x: abs(x['Prob'] - 0.5)  # 极端值优先
    }
    
    sort_key = sort_key_map.get(ORDER_BY, sort_key_map['volume'])
    sorted_data = sorted(final_data, key=sort_key, reverse=True)
    
    # 应用 Vibe Filter (自定义或默认胜率区间)
    vibe_list = [r for r in sorted_data if r['Volume'] > MIN_VOLUME and MIN_PROB <= r['Prob'] <= MAX_PROB]
    
    # 统计被胜率/成交量过滤掉的数量 (用于诊断)
    filtered_count = len(sorted_data) - len(vibe_list)
    
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

    if filtered_count > 0 and MAX_DAYS_TO_END >= 0:
         console.print(f"[dim yellow]⚠️ 注意: 有 {filtered_count} 个符合日期但被胜率/成交量过滤的市场。如结果过少，请放宽胜率区间。[/dim yellow]")

    # 绘制 Rich 表格
    table = Table(title=f"{header}", border_style="cyan", header_style="bold magenta")
    table.add_column("侦察目标 (Market)", style="white")
    table.add_column("⏳ 剩", justify="right", style="yellow")
    table.add_column("胜率", justify="center", style="green")
    table.add_column("成交量", justify="right", style="blue")
    table.add_column("查看链接 (Link)", justify="left", style="underline cyan")

    for r in display_list:
        days_str = str(r['DaysToEnd']) if r['DaysToEnd'] < 900 else ">2y"
        table.add_row(
            r['Title'][:50],
            days_str + "d",
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

    # [Automation] Webhook 推送逻辑
    WEBHOOK_URL = os.getenv("SCOUT_WEBHOOK_URL", "").strip()
    if WEBHOOK_URL and display_list:
        try:
            console.print(f"\n[cyan]正在向 Webhook 推送 {len(display_list)} 条情报...[/cyan]")
            
            # 构造消息内容
            msg_content = f"🕵️ **Mikon Scout 侦察报告**\n"
            msg_content += f"🎯 目标: {tag_info}\n"
            msg_content += f"📊 规则: >${MIN_VOLUME:,.0f} | Win {MIN_PROB:.0%}-{MAX_PROB:.0%}\n"
            msg_content += f"⏱️ 耗时: {time.time()-start_t:.1f}s | 查获: {len(display_list)} 条\n\n"
            
            for i, r in enumerate(display_list[:10], 1): # 限制推送前10条以免刷屏
                msg_content += f"{i}. [{r['Prob']:.1%}] **{r['Title']}**\n"
                msg_content += f"   💰 ${r['Volume']:,.0f} | 🔗 <{r['Link']}>\n"
            
            if len(display_list) > 10:
                msg_content += f"\n...还有 {len(display_list)-10} 条见完整名单。"

            payload = {
                "content": msg_content,
                "username": "Mikon Scout Army"
            }
            
            # 发送
            requests.post(WEBHOOK_URL, json=payload, timeout=10)
            console.print("[bold green]✅ 推送成功！[/bold green]")
        except Exception as e:
            console.print(f"[red]❌ 推送失败: {e}[/red]")

if __name__ == "__main__":
    scout()
