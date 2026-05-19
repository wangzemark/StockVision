"""美股股票列表 — Wikipedia S&P 500 成分股，支持名称/代码模糊搜索。"""

import io
import json
import os
import threading
import time
import pandas as pd
import requests

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "us_stock_list_cache.json")
REFRESH_INTERVAL = 24 * 60 * 60

WIKI_SP500 = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

_stocks: list[dict] = []
_lock = threading.Lock()
_loaded = False


def _fetch_from_api() -> list[dict]:
    """从 Wikipedia 获取 S&P 500 成分股。"""
    resp = requests.get(WIKI_SP500, timeout=30, headers=_headers)
    resp.raise_for_status()
    tables = pd.read_html(io.StringIO(resp.text))
    df = tables[0]
    result = []
    for _, row in df.iterrows():
        symbol = str(row.get("Symbol", "")).strip().replace(".", "-")
        name = str(row.get("Security", "")).strip()
        if symbol and name:
            result.append({"code": symbol, "name": name})
    return result


def _load_cache() -> list[dict] | None:
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        stocks = data.get("stocks", [])
        if stocks:
            return stocks
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    return None


def _save_cache(stocks: list[dict]):
    data = {
        "updated_at": time.time(),
        "count": len(stocks),
        "stocks": stocks,
    }
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def refresh_us_stock_list():
    """从 API 刷新美股列表并写入缓存（阻塞调用）。"""
    global _stocks
    try:
        stocks = _fetch_from_api()
        _save_cache(stocks)
        with _lock:
            _stocks = stocks
        print(f"[us_stock_list] 已刷新 {len(stocks)} 只美股")
    except Exception as e:
        print(f"[us_stock_list] 刷新失败: {e}")
        cached = _load_cache()
        if cached:
            with _lock:
                _stocks = cached
            print(f"[us_stock_list] 回退到缓存 ({len(cached)} 只)")


def _ensure_loaded():
    global _loaded, _stocks
    if _loaded:
        return
    with _lock:
        if _loaded:
            return
        cached = _load_cache()
        if cached:
            _stocks = cached
            _loaded = True
            age = time.time() - (os.path.getmtime(CACHE_FILE) if os.path.exists(CACHE_FILE) else 0)
            if age > REFRESH_INTERVAL:
                t = threading.Thread(target=refresh_us_stock_list, daemon=True)
                t.start()
            return
        _loaded = True
    refresh_us_stock_list()


def search_us_stocks(query: str, limit: int = 10) -> list[dict]:
    """模糊搜索美股，返回 [{code, name, score}] 按相关度降序排列。"""
    _ensure_loaded()

    q = query.strip()
    if not q:
        return []

    q_lower = q.lower()
    q_upper = q.upper()
    scored = []

    with _lock:
        candidates = list(_stocks)

    for s in candidates:
        code = s["code"]
        name = s["name"]
        name_lower = name.lower()
        code_lower = code.lower()

        score = 0
        if q_upper == code.upper():
            score = 100
        elif q_lower == name_lower:
            score = 95
        elif code_lower.startswith(q_lower):
            score = 80
        elif name_lower.startswith(q_lower):
            score = 75
        elif q_lower in name_lower:
            score = 60
        elif q_lower in code_lower:
            score = 55
        else:
            idx = 0
            matched = True
            for ch in q_lower:
                idx = name_lower.find(ch, idx)
                if idx == -1:
                    matched = False
                    break
                idx += 1
            if matched:
                score = 40

        if score > 0:
            scored.append({"code": code, "name": name, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]
