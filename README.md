# StockVision

A股 & 美股实时分析仪表盘，兼具基本面与技术面，基于 Flask + ECharts 构建。

## 功能

- **实时行情** — 股价、涨跌幅、市盈率、市净率、ROE、EPS、换手率、市值等
- **技术指标** — MA（5/20/60）、MACD、RSI、布林带、年化波动率、最大回撤、夏普比率、趋势判断
- **K线可视化** — 日线前复权折线图 + MACD + RSI仪表盘 + 成交量柱状图
- **A股名称搜索** — 模糊匹配自动补全，支持名称、代码、字符顺序搜索（如输入"贵茅"即可找到"贵州茅台"）
- **美股支持** — 基于 Yahoo Finance，涵盖基本面与技术面

## 数据源

| 市场 | 行情数据 | 股票列表 |
|------|----------|----------|
| A股 | 腾讯财经 `qt.gtimg.cn` | 新浪财经 |
| 美股 | Yahoo Finance (`yfinance`) | — |

## 快速开始

```bash
pip install -r requirements_dashboard.txt
python stock_server.py
```

浏览器打开 `http://localhost:5000`（A股）或 `http://localhost:5000/us`（美股）。

## 项目结构

```
stock_server.py          # Flask API 入口
stock_data.py            # A股行情获取（腾讯财经）
stock_list.py            # A股股票列表 & 模糊搜索
us_stock_data.py         # 美股行情获取（yfinance）
stock_indicators.py      # 技术指标计算
static/
  dashboard.html         # A股仪表盘前端
  us_dashboard.html      # 美股仪表盘前端
```

## API

| 端点 | 说明 |
|------|------|
| `GET /api/stock/<code>/all` | A股基本面 + 技术面 |
| `GET /api/stock/<code>/fundamentals` | A股基本面 |
| `GET /api/stock/<code>/technical` | A股技术指标 |
| `GET /api/stock/search?q=<keyword>` | A股名称模糊搜索 |
| `GET /api/us/stock/<symbol>/all` | 美股基本面 + 技术面 |
| `GET /api/us/stock/<symbol>/fundamentals` | 美股基本面 |
| `GET /api/us/stock/<symbol>/technical` | 美股技术指标 |

---

# StockVision

A real-time stock analysis dashboard for Chinese A-shares and US stocks, combining fundamentals and technicals. Built with Flask + ECharts.

## Features

- **Real-time Quotes** — Price, change %, PE, PB, ROE, EPS, turnover rate, market cap, and more
- **Technical Indicators** — MA (5/20/60), MACD, RSI, Bollinger Bands, annualized volatility, max drawdown, Sharpe ratio, trend detection
- **Charting** — Daily candlestick line chart + MACD histogram + RSI gauge + volume bars
- **A-share Name Search** — Fuzzy autocomplete supporting name, code, and character-sequence matching (e.g. "贵茅" finds "贵州茅台")
- **US Stock Support** — Fundamentals and technicals via Yahoo Finance

## Data Sources

| Market | Quotes | Stock List |
|--------|--------|------------|
| A-shares | Tencent Finance `qt.gtimg.cn` | Sina Finance |
| US | Yahoo Finance (`yfinance`) | — |

## Quick Start

```bash
pip install -r requirements_dashboard.txt
python stock_server.py
```

Navigate to `http://localhost:5000` for A-shares or `http://localhost:5000/us` for US stocks.

## Project Structure

```
stock_server.py          # Flask API entry point
stock_data.py            # A-share quotes (Tencent Finance)
stock_list.py            # A-share stock list & fuzzy search
us_stock_data.py         # US stock quotes (yfinance)
stock_indicators.py      # Technical indicator calculations
static/
  dashboard.html         # A-share dashboard frontend
  us_dashboard.html      # US stock dashboard frontend
```

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/stock/<code>/all` | A-share fundamentals + technicals |
| `GET /api/stock/<code>/fundamentals` | A-share fundamentals |
| `GET /api/stock/<code>/technical` | A-share technical indicators |
| `GET /api/stock/search?q=<keyword>` | A-share name fuzzy search |
| `GET /api/us/stock/<symbol>/all` | US stock fundamentals + technicals |
| `GET /api/us/stock/<symbol>/fundamentals` | US stock fundamentals |
| `GET /api/us/stock/<symbol>/technical` | US stock technical indicators |
