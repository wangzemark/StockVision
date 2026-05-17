"""美股数据获取模块 — 基于 yfinance 封装 Yahoo Finance 数据。"""

import pandas as pd
import yfinance as yf


def fetch_realtime(symbol: str) -> dict:
    """获取美股实时行情和基础财务指标。

    symbol: 美股代码，如 'AAPL'、'MSFT'、'GOOGL'
    """
    sym = symbol.upper().strip()
    ticker = yf.Ticker(sym)

    try:
        info = ticker.info
    except Exception:
        info = {}

    def safe_float(v, default=None):
        try:
            return float(v)
        except (ValueError, TypeError):
            return default

    # 价格：优先用 currentPrice，其次 regularMarketPrice，最后 previousClose
    price = safe_float(info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose"))

    # 涨跌
    change_pct = safe_float(info.get("regularMarketChangePercent"))
    change_amount = safe_float(info.get("regularMarketChange"))

    return {
        "code": sym,
        "name": str(info.get("shortName") or info.get("longName") or sym),
        "price": price,
        "change_pct": change_pct,
        "change_amount": change_amount,
        "volume": safe_float(info.get("regularMarketVolume")),
        "amount": None,  # yfinance 不直接提供成交额
        "high": safe_float(info.get("regularMarketDayHigh") or info.get("dayHigh")),
        "low": safe_float(info.get("regularMarketDayLow") or info.get("dayLow")),
        "open": safe_float(info.get("regularMarketOpen") or info.get("open")),
        "pre_close": safe_float(info.get("previousClose") or info.get("regularMarketPreviousClose")),
        "turnover_rate": None,  # yfinance 不直接提供换手率
        "pe": safe_float(info.get("trailingPE")),
        "pb": safe_float(info.get("priceToBook")),
        "eps": safe_float(info.get("epsTrailingTwelveMonths")),
        "roe": safe_float(info.get("returnOnEquity")) * 100 if safe_float(info.get("returnOnEquity")) is not None else None,  # 转为百分比
        "market_cap": safe_float(info.get("marketCap")),
        "circ_market_cap": safe_float(info.get("marketCap")),  # yfinance 不区分流通市值
        # 美股额外字段
        "forward_pe": safe_float(info.get("forwardPE")),
        "beta": safe_float(info.get("beta")),
        "dividend_yield": safe_float(info.get("dividendYield")),
        "52w_high": safe_float(info.get("fiftyTwoWeekHigh")),
        "52w_low": safe_float(info.get("fiftyTwoWeekLow")),
        "sector": info.get("sector", ""),
        "industry": info.get("industry", ""),
    }


def fetch_history(symbol: str, period="1y", days=250) -> pd.DataFrame:
    """获取美股历史 K 线数据。

    返回标准列名: date, open, close, high, low, volume, amount
    """
    sym = symbol.upper().strip()
    ticker = yf.Ticker(sym)

    raw = ticker.history(period=period)

    if raw.empty:
        raise ValueError(f"未找到美股 {sym} 的历史数据，请检查代码是否正确")

    # yfinance 返回的 DataFrame 索引是带时区的 DatetimeIndex
    # 列名: Open, High, Low, Close, Volume, Dividends, Stock Splits
    raw = raw.reset_index()
    raw["Date"] = pd.to_datetime(raw["Date"]).dt.tz_localize(None)

    # 取最近 days 条
    raw = raw.tail(days).copy()

    df = pd.DataFrame({
        "date": raw["Date"],
        "open": raw["Open"].astype(float),
        "close": raw["Close"].astype(float),
        "high": raw["High"].astype(float),
        "low": raw["Low"].astype(float),
        "volume": raw["Volume"].astype(float),
    })
    df = df.reset_index(drop=True)

    if df.empty:
        raise ValueError(f"获取 {sym} 历史数据后为空")

    return df


def fetch_all(symbol: str) -> tuple:
    """合并获取基本面和技术面数据。"""
    fundamentals = fetch_realtime(symbol)
    df = fetch_history(symbol)
    return fundamentals, df
