# 🎯 Polymarket Scout

**Mikon AI Army 闪电侦察兵** - 高性能 Polymarket 市场情报系统

一个强大的 Polymarket 市场数据侦察工具，已升级为**全自动指挥系统**。支持可视化配置、方案预设、自动化推送以及一键闪电战。

## ✨ 核心特性

### 🎮 指挥系统 (Tactical Dashboard)

- **战术指挥中心 (Web UI)**：
  - **Grid 布局优化**：左侧配置，右侧结果，视野开阔，操控精准。
  - **战术方案管理**：一键保存/加载不同的侦察策略（如"金融套利"、"加密风暴"）。
  - **自动化与推送 (New!)**：
    - **默认启动预设**：设定 `start_scout.bat` 运行时自动加载的方案。
    - **Webhook 消息推送**：支持将侦察报告实时发送至 Discord / Slack / Telegram。
- **闪电侦察模式 (CLI/Auto)**：
  - **智能重定向**：运行 `start_scout.bat` 时自动读取 UI 设定的默认预设。
  - **极致效率**：30-60秒内完成深度扫描并推送情报。

### 🔍 全维侦察能力

- **成交量与流动性**：双重门槛过滤，锁定真正的高价值市场。
- **胜率区间锁定**：自定义胜率过滤，避开无效博弈或归零风险。
- **时效性追踪**：专注于短线结盘机会，提高资金周转率。
- **精准关键词与黑名单**：通过关键词定向爆破，并利用黑名单过滤干扰项。

## 🚀 快速开始

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

3. **启动指令**

- **方式一：启动可视化指挥中心 (管理配置)**
  运行 `start_ui.bat`，在浏览器中配置您的战术、预设及 Webhook。
- **方式二：执行自动化闪电战 (日常运行)**
  运行 `start_scout.bat`，系统将按您在 UI 中设定的**默认启动预设**自动执行侦察并推送结果。

## ⚙️ 核心参数详解

| 参数名              | 说明                         | 示例                          |
| :------------------ | :--------------------------- | :---------------------------- |
| `SCOUT_AUTO_PRESET` | 自动化模式默认加载的预设方案 | `金融套利`                    |
| `SCOUT_WEBHOOK_URL` | 接情报推送的 Webhook 地址    | `https://discord.com/api/...` |
| `SCOUT_TAG`         | 定向品类标签 ID 或名称       | `235` (Bitcoin)               |
| `SCOUT_MIN_VOLUME`  | 最低成交量门槛 (USD)         | `1000`                        |
| `SCOUT_SEARCH`      | 包含以下任一关键词即保留     | `Earnings, Airdrop`           |

## 📁 项目结构

```
polymarket-scout/
├── static/               # [Web] 前端战术指挥中心
├── presets/              # [Data] 战术方案预设存储 (JSON)
├── server.py             # [Core] Web 指挥中心后端
├── scout.py              # [Core] 核心侦察引擎 (支持自动化覆盖)
├── .env                  # [Config] 核心运行配置
├── start_ui.bat          # [Script] 启动 UI 模式
├── start_scout.bat       # [Script] 执行自动化侦察
└── markets_list.txt      # [Output] 侦察快照输出
```

## 📝 输出示例

系统将侦察前 10 条高价值情报通过 Webhook 推送，格式如下：

> 🕵️ **Mikon Scout 侦察报告**
> 🎯 目标: 金融套利
> 📊 规则: >$1,000 | Win 1%-99%
>
> 1. [65.0%] **NVIDIA Earnings Beat?**
>    💰 $150,000 | 🔗 <链接>

---

**Mikon AI Army** - 为 Vibe 而战 🚀
