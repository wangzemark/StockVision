"""A股股票列表 — 从新浪财经获取名称→代码映射，支持模糊搜索。"""

import json
import os
import threading
import time
import requests

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stock_list_cache.json")
REFRESH_INTERVAL = 24 * 60 * 60  # 24 hours

SINA_API = (
    "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
    "Market_Center.getHQNodeDataSimple"
    "?page=1&num=6000&sort=symbol&asc=1&node=hs_a"
)

_stocks: list[dict] = []  # [{code, name}]
_lock = threading.Lock()
_loaded = False


def _fetch_from_api() -> list[dict]:
    """从新浪 API 拉取全量 A 股股票列表。"""
    resp = requests.get(SINA_API, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    raw = resp.json()
    result = []
    for item in raw:
        code = item.get("code", "")
        name = item.get("name", "")
        if code and name and len(code) == 6:
            result.append({"code": code, "name": name})
    return result


def _load_cache() -> list[dict] | None:
    """读取本地缓存，若有效返回列表否则返回 None。"""
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
    """写入本地缓存。"""
    data = {
        "updated_at": time.time(),
        "count": len(stocks),
        "stocks": stocks,
    }
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def refresh_stock_list():
    """从 API 刷新股票列表并写入缓存（阻塞调用）。"""
    global _stocks
    try:
        stocks = _fetch_from_api()
        _save_cache(stocks)
        with _lock:
            _stocks = stocks
        print(f"[stock_list] 已刷新 {len(stocks)} 只股票")
    except Exception as e:
        print(f"[stock_list] 刷新失败: {e}")
        # 回退到缓存
        cached = _load_cache()
        if cached:
            with _lock:
                _stocks = cached
            print(f"[stock_list] 回退到缓存 ({len(cached)} 只)")


def _ensure_loaded():
    """确保股票列表已加载（首次调用时触发）。"""
    global _loaded
    if _loaded:
        return
    with _lock:
        if _loaded:
            return
        # 优先读缓存
        cached = _load_cache()
        if cached:
            _stocks = cached
            _loaded = True
            age = time.time() - (os.path.getmtime(CACHE_FILE) if os.path.exists(CACHE_FILE) else 0)
            # 缓存过期则后台刷新
            if age > REFRESH_INTERVAL:
                t = threading.Thread(target=refresh_stock_list, daemon=True)
                t.start()
            return
        _loaded = True
    # 无缓存时同步拉取
    refresh_stock_list()


def search_stocks(query: str, limit: int = 10) -> list[dict]:
    """模糊搜索股票，返回 [{code, name, score}] 按相关度降序排列。"""
    _ensure_loaded()

    q = query.strip()
    if not q:
        return []

    q_lower = q.lower()
    scored = []

    with _lock:
        candidates = list(_stocks)

    for s in candidates:
        code = s["code"]
        name = s["name"]
        name_lower = name.lower()
        code_lower = code.lower()

        score = 0
        if q_lower == code_lower:
            score = 100
        elif q_lower == name_lower:
            score = 95
        elif name_lower.startswith(q_lower):
            score = 80
        elif code_lower.startswith(q_lower):
            score = 75
        elif q_lower in name_lower:
            score = 60
        elif q_lower in code_lower:
            score = 55
        else:
            # 字符顺序匹配：query 的每个字符按顺序出现在 name 中
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
