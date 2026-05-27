"""Flask API 服务 — 为仪表盘提供股票数据接口。"""

import traceback
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# 导入 A 股数据模块：实时行情、历史K线、综合数据
from stock_data import fetch_realtime, fetch_history, fetch_all
# 导入 A 股股票列表：模糊搜索、列表刷新
from stock_list import search_stocks, refresh_stock_list
# 导入美股数据模块（用 us_ 前缀区分，避免和 A 股函数重名）
from us_stock_data import fetch_realtime as us_fetch_realtime
from us_stock_data import fetch_history as us_fetch_history
from us_stock_data import fetch_all as us_fetch_all
# 导入美股股票列表
from us_stock_list import search_us_stocks, refresh_us_stock_list
# 导入技术指标计算模块（A股和美股共用同一个计算逻辑）
from stock_indicators import compute_all_technical

# 创建 Flask 应用实例
# static_folder="static"  → 静态文件（HTML/JS/CSS）放在 static/ 目录下
# static_url_path=""      → 静态文件直接通过根路径访问，如 /dashboard.html
app = Flask(__name__, static_folder="static", static_url_path="")
# 启用跨域资源共享，允许前端页面从任何来源调用 API
CORS(app)


# ============================================================
#  页面路由 — 返回 HTML 页面
# ============================================================

@app.route("/")  # 访问根路径 → 返回 A 股仪表盘页面
def index():
    return send_from_directory("static", "dashboard.html")


# ============================================================
#  A 股 API — 提供 A 股股票数据
# ============================================================

@app.route("/api/stock/<code>/fundamentals")
# <code> 是路径参数，Flask 会自动提取 URL 中的股票代码传给函数
# 例如访问 /api/stock/000001/fundamentals → code = "000001"
def api_fundamentals(code):
    """获取 A 股基本面数据：当前价、涨跌幅、PE、PB、市值等。"""
    try:
        data = fetch_realtime(code)  # 调用 stock_data 模块抓取实时数据
        return jsonify({"ok": True, "data": data})  # 把 Python 字典转成 JSON 返回
    except Exception as e:
        # 出错了返回错误信息，HTTP 状态码 400 表示客户端请求有误
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/stock/<code>/technical")
def api_technical(code):
    """获取 A 股技术指标和 K 线图数据：MA、MACD、RSI、布林带等。"""
    try:
        df = fetch_history(code)         # 拉取历史 K 线数据（DataFrame 格式）
        tech = compute_all_technical(df)  # 基于 K 线计算所有技术指标
        dates = [str(d.date()) for d in df["date"]]  # 把日期转成字符串列表
        result = {
            # ── 摘要指标（最新值） ──
            "ma": tech["ma"],                  # 均线（MA5/MA20/MA60 最新值）
            "macd": {k: tech["macd"][k] for k in ["dif", "dea", "hist"]},  # MACD 最新值
            "rsi": tech["rsi"],                # RSI 相对强弱指标（0-100）
            "boll": tech["boll"],              # 布林带（上轨/中轨/下轨最新值）
            "volatility": tech["volatility"],  # 历史波动率
            "max_drawdown": tech["max_drawdown"],  # 最大回撤
            "sharpe": tech["sharpe"],          # 夏普比率（风险调整后收益）
            "trend": tech["trend"],            # 趋势判断（上涨/下跌/震荡）
            # ── 图表数据（最近 180 个交易日，给前端画 K 线图用） ──
            "chart": {
                "dates": dates[-180:],         # X 轴日期
                "open": [round(float(x), 2) for x in df["open"].tail(180)],
                "close": [round(float(x), 2) for x in df["close"].tail(180)],
                "high": [round(float(x), 2) for x in df["high"].tail(180)],
                "low": [round(float(x), 2) for x in df["low"].tail(180)],
                "volume": [round(float(x), 0) for x in df["volume"].tail(180)],  # 成交量取整
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
        traceback.print_exc()  # 在服务器控制台打印完整错误堆栈，方便调试
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/stock/<code>/all")
def api_all(code):
    """获取 A 股全部数据（基本面 + 技术指标 + 图表），一次请求搞定。"""
    try:
        fundamentals, df = fetch_all(code)  # 同时返回基本面和 K 线数据
        tech = compute_all_technical(df)
        dates = [str(d.date()) for d in df["date"]]
        return jsonify({
            "ok": True,
            "data": {
                "fundamentals": fundamentals,  # 基本面：当前价、PE、PB 等
                "technical": {                 # 技术指标摘要
                    "ma": tech["ma"],
                    "macd": {k: tech["macd"][k] for k in ["dif", "dea", "hist"]},
                    "rsi": tech["rsi"],
                    "boll": tech["boll"],
                    "volatility": tech["volatility"],
                    "max_drawdown": tech["max_drawdown"],
                    "sharpe": tech["sharpe"],
                    "trend": tech["trend"],
                },
                "chart": {                     # 图表数据（最近 180 天）
                    "dates": dates[-180:],
                    "open": [round(float(x), 2) for x in df["open"].tail(180)],
                    "close": [round(float(x), 2) for x in df["close"].tail(180)],
                    "high": [round(float(x), 2) for x in df["high"].tail(180)],
                    "low": [round(float(x), 2) for x in df["low"].tail(180)],
                    "volume": [round(float(x), 0) for x in df["volume"].tail(180)],
                    # /all 接口只返回 MACD 曲线，不含 MA 和布林带（前端按需取用）
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
    """股票名称/代码模糊搜索，前端输入框的自动补全功能。"""
    q = request.args.get("q", "").strip()  # 从 URL 查询参数 ?q=xxx 获取搜索词
    if len(q) < 1:
        return jsonify({"ok": True, "data": []})  # 空搜索词直接返回空列表
    results = search_stocks(q, limit=10)  # 最多返回 10 条匹配结果
    return jsonify({"ok": True, "data": results})


# ============================================================
#  美股 API — 和 A 股结构完全对称，只是数据源换成美股模块
# ============================================================

@app.route("/us")
def us_index():
    """美股仪表盘页面。"""
    return send_from_directory("static", "us_dashboard.html")


@app.route("/api/us/stock/search")
def api_us_stock_search():
    """美股名称/代码模糊搜索。"""
    q = request.args.get("q", "").strip()
    if len(q) < 1:
        return jsonify({"ok": True, "data": []})
    results = search_us_stocks(q, limit=10)
    return jsonify({"ok": True, "data": results})


@app.route("/api/us/stock/<symbol>/fundamentals")
def api_us_fundamentals(symbol):
    """获取美股基本面数据。"""
    try:
        data = us_fetch_realtime(symbol)  # 调用美股数据模块
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/us/stock/<symbol>/technical")
def api_us_technical(symbol):
    """获取美股技术指标和 K 线图数据。"""
    try:
        df = us_fetch_history(symbol)
        tech = compute_all_technical(df)  # 技术指标计算函数和 A 股是同一个
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


@app.route("/api/us/stock/<symbol>/all")
def api_us_all(symbol):
    """获取美股全部数据（基本面 + 技术指标 + 图表）。"""
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


# ============================================================
#  启动入口 — 只有直接运行 python stock_server.py 时才会执行
#  如果是被 import 导入的，__name__ 就不是 "__main__"，不会启动服务器
# ============================================================
if __name__ == "__main__":
    import threading

    host = "0.0.0.0"  # 监听所有网络接口，局域网内其他设备也能访问
    port = 5000       # Flask 默认端口

    # 启动后台线程，异步刷新股票列表缓存
    # daemon=True 表示主线程退出时这些线程也会自动结束
    threading.Thread(target=refresh_stock_list, daemon=True).start()
    threading.Thread(target=refresh_us_stock_list, daemon=True).start()

    # 打印启动信息，方便开发者知道该打开哪个地址
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
    # 启动 Flask 开发服务器
    # debug=True   → 开启调试模式，出错时在浏览器显示详细堆栈
    # use_reloader=False → 关闭自动重载，避免启动两次（改代码后需手动重启）
    app.run(debug=True, host=host, port=port, use_reloader=False)
