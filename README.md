# 🎯 Polymarket Scout

**Mikon AI Army 闪电侦察兵** - 高性能 Polymarket 市场情报系统

一个强大的 Polymarket 市场数据侦察工具，支持多维度筛选、智能品类识别和自定义排序策略。

## ✨ 核心特性

### 🔍 多维度筛选

- **成交量过滤**：设定最低成交量门槛，过滤低活跃市场
- **胜率区间**：自定义胜率范围（默认 15%-85%），避开极端市场
- **流动性检测**：排除订单簿深度不足的"僵尸市场"
- **日期倒计时**：专注于 X 天内即将结盘的短线机会
- **关键词搜索**：精准定位特定主题市场（如 "Trump", "Bitcoin"）

### 🎨 智能品类识别

自动匹配 Polymarket 官方品类标签：

- Sports（体育）
- Crypto（加密货币）
- Politics（政治）
- Business（商业）
- Pop Culture（流行文化）
- 更多...

### 📊 自定义排序

- `volume` - 按成交量排序（默认）
- `liquidity` - 按流动性排序
- `endDate` - 按即将到期排序
- `prob` - 按胜率极端值排序

### ⚡ 性能优化

- 30 秒闪电扫描
- 实时进度反馈
- Windows 终端输出优化
- 自动链接修复（避免 404）

## 🚀 快速开始

### 环境要求

- Python 3.7+
- Windows / macOS / Linux

### 安装步骤

1. **克隆仓库**

```bash
git clone <your-repo-url>
cd polymarket-scout
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **配置参数**

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，根据需求调整筛选参数
```

4. **启动侦察**

```bash
# Windows
start.bat

# Linux/macOS
python scout.py
```

## ⚙️ 配置说明

编辑 `.env` 文件进行个性化配置：

### 核心筛选规则

```bash
# 最低成交量（USD）
SCOUT_MIN_VOLUME=5000

# 胜率区间（0.0-1.0）
SCOUT_MIN_PROB=0.15
SCOUT_MAX_PROB=0.85

# 品类定向（留空 = 全局扫描）
SCOUT_TAG=Sports
```

### 高级筛选（可选）

```bash
# 最低流动性（留空 = 不限制）
SCOUT_MIN_LIQUIDITY=50000

# 结束日期倒计时（天数，留空 = 不限制）
SCOUT_MAX_DAYS_TO_END=7

# 关键词搜索（留空 = 不过滤）
SCOUT_SEARCH=Trump

# 排序策略
SCOUT_ORDER_BY=volume
```

### 运行参数

```bash
# API 抓取上限
SCOUT_FETCH_LIMIT=200

# 运行限时（秒）
SCOUT_RUNTIME_LIMIT=30
```

## 📖 使用示例

### 场景 1：短线狙击

寻找 3 天内结盘且流动性充足的市场：

```bash
SCOUT_MAX_DAYS_TO_END=3
SCOUT_MIN_LIQUIDITY=50000
SCOUT_ORDER_BY=endDate
```

### 场景 2：热点追踪

专注于政治类 Trump 相关市场：

```bash
SCOUT_TAG=Politics
SCOUT_SEARCH=Trump
SCOUT_ORDER_BY=volume
```

### 场景 3：冷门深挖

寻找流动性适中的小众市场：

```bash
SCOUT_MIN_LIQUIDITY=5000
SCOUT_MIN_VOLUME=10000
SCOUT_ORDER_BY=prob
```

## 📁 项目结构

```
polymarket-scout/
├── scout.py              # 主侦察脚本
├── debug_api.py          # API 调试工具
├── start.bat             # Windows 快速启动
├── requirements.txt      # Python 依赖
├── .env                  # 配置文件（不提交）
├── .env.example          # 配置模板
├── .gitignore           # Git 忽略规则
└── README.md            # 项目说明
```

## 🛠️ 调试工具

如需调试 API 响应结构：

```bash
python debug_api.py
```

将生成 `api_dump.json` 供分析使用。

## 📝 输出说明

运行后会生成 `markets_list.txt`，包含：

- 侦察时间戳
- 符合条件的市场总数
- 每个市场的详细信息（标题、胜率、成交量、链接）

## ⚠️ 注意事项

1. **API 限制**：Polymarket Gamma API 有频率限制（约 300 次/10秒），脚本已做优化
2. **数据延迟**：API 数据可能有数秒延迟，不适用于高频交易
3. **链接格式**：使用 `/market/` 前缀确保链接可访问

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**Mikon AI Army** - 为 Vibe 而战 🚀
