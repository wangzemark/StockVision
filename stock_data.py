"""A股数据获取模块 — 基于腾讯财经 HTTP API 封装。"""

import re
import pandas as pd
import requests


# ── 辅助函数 ──────────────────────────────────────────────

def _market(code: str):
    """根据代码返回 sz 或 sh。"""
    return "sh" if code.startswith(("6", "9")) else "sz"


def _safe_float(v, default=None):
    try:
        return round(float(v), 4)
    except (ValueError, TypeError):
        return default


# ── 实时行情 ──────────────────────────────────────────────

def fetch_realtime(code: str) -> dict:
    """获取实时行情和基础财务指标。

    code: 6位数字代码，如 '600519'、'000001'
    """
    mkt = _market(code)
    symbol = f"{mkt}{code}"

    # 1. 腾讯实时行情接口
    try:
        url = f"https://qt.gtimg.cn/q={symbol}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        raw = resp.text
        # 提取 var 赋值语句中的引号内容
        match = re.search(r'"([^"]*)"', raw)
        if not match:
            raise ValueError(f"未找到股票 {code} 的行情数据")
        parts = match.group(1).split("~")
    except Exception as e:
        raise ValueError(f"获取 {code} 实时行情失败: {e}")

    # 腾讯实时行情字段索引（~ 分隔，v2 格式共 88 字段）
    # [1]名称 [2]代码 [3]最新价 [4]昨收 [5]今开 [6]成交量(手)
    # [31]涨跌额 [32]涨跌幅% [33]最高 [34]最低
    # [38]换手率% [39]市盈率 [44]总市值(亿) [45]流通市值(亿) [46]市净率
    # [57]成交额(万)

    def field(i):
        return parts[i] if i < len(parts) and parts[i] else None

    # 2. 财务指标（PE/PB/EPS/ROE 从腾讯概况接口获取更准确）
    pe = _safe_float(field(39))
    pb = _safe_float(field(46))
    try:
        fin_url = f"https://ifzq.gtimg.cn/appstock/app/stockinfo/jiankuang?code={symbol}"
        fin_resp = requests.get(fin_url, timeout=10)
        if fin_resp.status_code == 200:
            fin = fin_resp.json()
            detail = fin.get("data", {}).get("zyzb", {}).get("detail", {})
            pe = _safe_float(detail.get("syl")) or pe
            pb = _safe_float(detail.get("sjl")) or pb
            eps = _safe_float(str(detail.get("mgsy", "")).replace("元", ""))
            roe = _safe_float(str(detail.get("jzcsyl", "")).replace("%", ""))
        else:
            eps = None
            roe = None
    except Exception:
        eps = None
        roe = None

    market_cap = _safe_float(field(44))  # 亿
    circ_market_cap = _safe_float(field(45))  # 亿

    return {
        "code": code,
        "name": str(field(1) or ""),
        "price": _safe_float(field(3)),
        "change_pct": _safe_float(field(32)),
        "change_amount": _safe_float(field(31)),
        "volume": _safe_float(field(6)),
        "amount": _safe_float(field(57)),  # 万元
        "high": _safe_float(field(33)),
        "low": _safe_float(field(34)),
        "open": _safe_float(field(5)),
        "pre_close": _safe_float(field(4)),
        "turnover_rate": _safe_float(field(38)),
        "pe": pe,
        "pb": pb,
        "eps": eps,
        "roe": roe,
        "market_cap": market_cap,  # 亿
        "circ_market_cap": circ_market_cap,  # 亿
    }


# ── 历史 K 线 ──────────────────────────────────────────────

def fetch_history(code: str, period="day", days=250) -> pd.DataFrame:
    """获取历史 K 线数据。

    返回标准列名: date, open, close, high, low, volume
    """
    mkt = _market(code)
    symbol = f"{mkt}{code}"

    try:
        url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={symbol},day,,,{days},qfq"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise ValueError(f"接口返回错误: {data.get('msg', '未知错误')}")

        # 数据路径: data[symbol]['qfqday'] 或 data[symbol]['day']
        stock_data = data.get("data", {}).get(symbol, {})
        rows = stock_data.get("qfqday") or stock_data.get("day") or []
        if not rows:
            raise ValueError(f"未找到 {code} 的历史数据")
    except Exception as e:
        raise ValueError(f"获取 {code} 历史K线失败: {e}")

    # 每条记录前6列: [date, open, close, high, low, volume]，含分红日会有第7列(dict)
    rows = [r[:6] for r in rows]
    df = pd.DataFrame(rows, columns=["date", "open", "close", "high", "low", "volume"])
    df["date"] = pd.to_datetime(df["date"])
    for col in ["open", "close", "high", "low", "volume"]:
        df[col] = df[col].astype(float)
    df = df.reset_index(drop=True)
    return df


# ── 合并接口 ──────────────────────────────────────────────

def fetch_all(code: str) -> tuple:
    """合并获取基本面和技术面数据。"""
    fundamentals = fetch_realtime(code)
    df = fetch_history(code)
    return fundamentals, df
