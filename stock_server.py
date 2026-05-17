"""Flask API 服务 — 为仪表盘提供股票数据接口。"""

import traceback
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from stock_data import fetch_realtime, fetch_history, fetch_all
from stock_list import search_stocks, refresh_stock_list
from us_stock_data import fetch_realtime as us_fetch_realtime
from us_stock_data import fetch_history as us_fetch_history
from us_stock_data import fetch_all as us_fetch_all
from stock_indicators import compute_all_technical

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)


@app.route("/")
def index():
    return send_from_directory("static", "dashboard.html")


@app.route("/api/stock/<code>/fundamentals")
def api_fundamentals(code):
    try:
        data = fetch_realtime(code)
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/stock/<code>/technical")
def api_technical(code):
    try:
        df = fetch_history(code)
        tech = compute_all_technical(df)
        dates = [str(d.date()) for d in df["date"]]
        result = {
            "ma": tech["ma"],
            "macd": {k: tech["macd"][k] for k in ["dif", "dea", "hist"]},
            "rsi": tech["rsi"],
            "boll": tech["boll"],
            "volatility": tech["volatility"],
            "max_drawdown": tech["max_drawdown"],
            "sharpe": tech["sharpe"],
            "trend": tech["trend"],
            # chart data
            "chart": {
                "dates": dates[-180:],
                "open": [round(float(x), 2) for x in df["open"].tail(180)],
                "close": [round(float(x), 2) for x in df["close"].tail(180)],
                "high": [round(float(x), 2) for x in df["high"].tail(180)],
                "low": [round(float(x), 2) for x in df["low"].tail(180)],
                "volume": [round(float(x), 0) for x in df["volume"].tail(180)],
                "ma5": tech["ma"].get("ma5"),
                "ma20": tech["ma"].get("ma20"),
                "ma60": tech["ma"].get("ma60"),
                "boll_upper": tech["boll"]["upper"],
                "boll_middle": tech["boll"]["middle"],
                "boll_lower": tech["boll"]["lower"],
                "macd_dif": tech["macd_series"]["dif"],
                "macd_dea": tech["macd_series"]["dea"],
                "macd_hist": tech["macd_series"]["hist"],
            },
        }
        return jsonify({"ok": True, "data": result})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/stock/<code>/all")
def api_all(code):
    try:
        fundamentals, df = fetch_all(code)
        tech = compute_all_technical(df)
        dates = [str(d.date()) for d in df["date"]]
        return jsonify({
            "ok": True,
            "data": {
                "fundamentals": fundamentals,
                "technical": {
                    "ma": tech["ma"],
                    "macd": {k: tech["macd"][k] for k in ["dif", "dea", "hist"]},
                    "rsi": tech["rsi"],
                    "boll": tech["boll"],
                    "volatility": tech["volatility"],
                    "max_drawdown": tech["max_drawdown"],
                    "sharpe": tech["sharpe"],
                    "trend": tech["trend"],
                },
                "chart": {
                    "dates": dates[-180:],
                    "open": [round(float(x), 2) for x in df["open"].tail(180)],
                    "close": [round(float(x), 2) for x in df["close"].tail(180)],
                    "high": [round(float(x), 2) for x in df["high"].tail(180)],
                    "low": [round(float(x), 2) for x in df["low"].tail(180)],
                    "volume": [round(float(x), 0) for x in df["volume"].tail(180)],
                    "macd_dif": tech["macd_series"]["dif"],
                    "macd_dea": tech["macd_series"]["dea"],
                    "macd_hist": tech["macd_series"]["hist"],
                },
            },
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/stock/search")
def api_stock_search():
    """股票名称/代码模糊搜索。"""
    q = request.args.get("q", "").strip()
    if len(q) < 1:
        return jsonify({"ok": True, "data": []})
    results = search_stocks(q, limit=10)
    return jsonify({"ok": True, "data": results})


# ── 美股 API ──────────────────────────────────────────────

@app.route("/us")
def us_index():
    return send_from_directory("static", "us_dashboard.html")


@app.route("/api/us/stock/<symbol>/fundamentals")
def api_us_fundamentals(symbol):
    try:
        data = us_fetch_realtime(symbol)
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/us/stock/<symbol>/technical")
def api_us_technical(symbol):
    try:
        df = us_fetch_history(symbol)
        tech = compute_all_technical(df)
        dates = [str(d.date()) for d in df["date"]]
        result = {
            "ma": tech["ma"],
            "macd": {k: tech["macd"][k] for k in ["dif", "dea", "hist"]},
            "rsi": tech["rsi"],
            "boll": tech["boll"],
            "volatility": tech["volatility"],
            "max_drawdown": tech["max_drawdown"],
            "sharpe": tech["sharpe"],
            "trend": tech["trend"],
            "chart": {
                "dates": dates[-180:],
                "close": [round(float(x), 2) for x in df["close"].tail(180)],
                "volume": [round(float(x), 0) for x in df["volume"].tail(180)],
                "ma5": tech["ma"].get("ma5"),
                "ma20": tech["ma"].get("ma20"),
                "ma60": tech["ma"].get("ma60"),
                "boll_upper": tech["boll"]["upper"],
                "boll_middle": tech["boll"]["middle"],
                "boll_lower": tech["boll"]["lower"],
                "macd_dif": tech["macd_series"]["dif"],
                "macd_dea": tech["macd_series"]["dea"],
                "macd_hist": tech["macd_series"]["hist"],
            },
        }
        return jsonify({"ok": True, "data": result})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/us/stock/<symbol>/all")
def api_us_all(symbol):
    try:
        fundamentals, df = us_fetch_all(symbol)
        tech = compute_all_technical(df)
        dates = [str(d.date()) for d in df["date"]]
        return jsonify({
            "ok": True,
            "data": {
                "fundamentals": fundamentals,
                "technical": {
                    "ma": tech["ma"],
                    "macd": {k: tech["macd"][k] for k in ["dif", "dea", "hist"]},
                    "rsi": tech["rsi"],
                    "boll": tech["boll"],
                    "volatility": tech["volatility"],
                    "max_drawdown": tech["max_drawdown"],
                    "sharpe": tech["sharpe"],
                    "trend": tech["trend"],
                },
                "chart": {
                    "dates": dates[-180:],
                    "close": [round(float(x), 2) for x in df["close"].tail(180)],
                    "volume": [round(float(x), 0) for x in df["volume"].tail(180)],
                    "macd_dif": tech["macd_series"]["dif"],
                    "macd_dea": tech["macd_series"]["dea"],
                    "macd_hist": tech["macd_series"]["hist"],
                },
            },
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 400


if __name__ == "__main__":
    import threading

    host = "0.0.0.0"
    port = 5000

    # 后台异步刷新股票列表
    threading.Thread(target=refresh_stock_list, daemon=True).start()

    print()
    print("=" * 56)
    print("  股票分析仪表盘")
    print("=" * 56)
    print(f"  启动地址: http://127.0.0.1:{port}")
    print()
    print(f"  A股 仪表盘  → http://127.0.0.1:{port}/")
    print(f"  美股 仪表盘  → http://127.0.0.1:{port}/us")
    print()
    print(f"  A股 API 示例 → http://127.0.0.1:{port}/api/stock/000001/all")
    print(f"  美股 API 示例 → http://127.0.0.1:{port}/api/us/stock/AAPL/all")
    print("=" * 56)
    print()
    app.run(debug=True, host=host, port=port)
