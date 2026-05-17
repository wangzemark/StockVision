"""技术指标计算模块 — 纯函数，不依赖外部数据源。"""

import numpy as np
import pandas as pd


def calc_ma(close: pd.Series, periods=(5, 20, 60)) -> dict:
    """计算均线。"""
    result = {}
    for p in periods:
        ma = close.rolling(window=p).mean()
        result[f"ma{p}"] = round(float(ma.iloc[-1]), 2) if not pd.isna(ma.iloc[-1]) else None
    return result


def calc_macd(close: pd.Series, fast=12, slow=26, signal=9) -> dict:
    """计算 MACD。"""
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    hist = (dif - dea) * 2
    return {
        "dif": round(float(dif.iloc[-1]), 4),
        "dea": round(float(dea.iloc[-1]), 4),
        "hist": round(float(hist.iloc[-1]), 4),
        "dif_series": [round(float(x), 4) if not pd.isna(x) else None for x in dif.tail(120)],
        "dea_series": [round(float(x), 4) if not pd.isna(x) else None for x in dea.tail(120)],
        "hist_series": [round(float(x), 4) if not pd.isna(x) else None for x in hist.tail(120)],
    }


def calc_rsi(close: pd.Series, period=14) -> float:
    """计算 RSI。"""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi.iloc[-1]), 2)


def calc_bollinger(close: pd.Series, period=20, std=2) -> dict:
    """计算布林带。"""
    middle = close.rolling(window=period).mean()
    std_dev = close.rolling(window=period).std()
    upper = middle + std * std_dev
    lower = middle - std * std_dev
    return {
        "upper": round(float(upper.iloc[-1]), 2) if not pd.isna(upper.iloc[-1]) else None,
        "middle": round(float(middle.iloc[-1]), 2) if not pd.isna(middle.iloc[-1]) else None,
        "lower": round(float(lower.iloc[-1]), 2) if not pd.isna(lower.iloc[-1]) else None,
    }


def calc_volatility(close: pd.Series, trading_days=252) -> float:
    """计算年化波动率。"""
    returns = close.pct_change().dropna()
    vol = returns.std() * np.sqrt(trading_days)
    return round(float(vol), 4)


def calc_max_drawdown(close: pd.Series) -> float:
    """计算最大回撤（百分比）。"""
    peak = close.expanding().max()
    drawdown = (close - peak) / peak
    return round(float(drawdown.min()), 4)


def calc_sharpe(close: pd.Series, risk_free=0.025, trading_days=252) -> float:
    """计算年化夏普比率。"""
    returns = close.pct_change().dropna()
    excess = returns.mean() * trading_days - risk_free
    vol = returns.std() * np.sqrt(trading_days)
    if vol == 0:
        return 0.0
    return round(float(excess / vol), 4)


def detect_trend(close: pd.Series) -> str:
    """判断当前趋势方向。"""
    ma5 = close.rolling(5).mean().iloc[-1]
    ma20 = close.rolling(20).mean().iloc[-1]
    ma60 = close.rolling(60).mean().iloc[-1]
    current = close.iloc[-1]

    if current > ma5 > ma20 > ma60:
        return "上升趋势（多头排列）"
    elif current < ma5 < ma20 < ma60:
        return "下降趋势（空头排列）"
    elif current > ma60:
        return "震荡偏多"
    elif current < ma60:
        return "震荡偏空"
    return "横盘整理"


def compute_all_technical(df: pd.DataFrame) -> dict:
    """从历史 K 线 DataFrame 计算所有技术指标。

    df 需包含列: date, open, close, high, low, volume
    """
    close = df["close"]

    result = {
        "ma": calc_ma(close),
        "macd": calc_macd(close),
        "rsi": calc_rsi(close),
        "boll": calc_bollinger(close),
        "volatility": calc_volatility(close),
        "max_drawdown": calc_max_drawdown(close),
        "sharpe": calc_sharpe(close),
        "trend": detect_trend(close),
    }
    # MACD series are large, keep them separate for the chart
    result["macd_series"] = {
        "dif": result["macd"].pop("dif_series"),
        "dea": result["macd"].pop("dea_series"),
        "hist": result["macd"].pop("hist_series"),
    }
    return result
