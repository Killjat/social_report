from flask import Flask, render_template, jsonify, request
import json
import os
import asyncio
import threading
import time
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

# 收集状态
collection_status = {
    "running": False,
    "last_run": None,
    "last_count": 0,
    "error": None
}

def run_collection():
    """在后台线程中运行情报收集"""
    from main import IntelligenceProcessor

    collection_status["running"] = True
    collection_status["error"] = None
    print(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] 开始自动收集...")

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        processor = IntelligenceProcessor()
        results = loop.run_until_complete(processor.run())
        loop.close()

        collection_status["last_count"] = len(results)
        collection_status["last_run"] = datetime.now().isoformat()
        print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] 收集完成，共 {len(results)} 条")
    except Exception as e:
        collection_status["error"] = str(e)
        print(f"❌ 收集失败: {e}")
    finally:
        collection_status["running"] = False

def auto_collect_loop(interval_minutes=60):
    """定时自动收集，启动后立即跑一次，之后每隔 interval_minutes 分钟跑一次"""
    while True:
        if not collection_status["running"]:
            t = threading.Thread(target=run_collection, daemon=True)
            t.start()
            t.join()
        time.sleep(interval_minutes * 60)

def start_background_collector(interval_minutes=60):
    """启动后台定时收集线程"""
    t = threading.Thread(target=auto_collect_loop, args=(interval_minutes,), daemon=True)
    t.start()
    print(f"⏰ 后台收集已启动，每 {interval_minutes} 分钟自动收集一次")


@app.route('/')
def index():
    return render_template('dashboard.html')


@app.route('/api/data')
def get_data():
    data_dir = Path('.')
    json_files = list(data_dir.glob('intelligence_*.json'))

    if not json_files:
        return jsonify({"error": "No data found", "data": []})

    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)

    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            raw = json.load(f)
    except Exception as e:
        return jsonify({"error": str(e), "data": []})

    # 兼容新格式 {summary, items} 和旧格式 [...]
    data = raw.get('items', raw) if isinstance(raw, dict) else raw

    return jsonify({
        "filename": latest_file.name,
        "updated": datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat(),
        "data": data
    })


@app.route('/api/stats')
def get_stats():
    data_dir = Path('.')
    json_files = list(data_dir.glob('intelligence_*.json'))

    if not json_files:
        return jsonify({
            "total_items": 0,
            "by_platform": {},
            "by_keyword": {},
            "video_count": 0,
            "top_content": [],
            "collection_status": collection_status
        })

    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)

    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            raw = json.load(f)
    except Exception:
        raw = {}

    # 新格式直接用 summary，旧格式重新计算
    if isinstance(raw, dict) and 'summary' in raw:
        stats = raw['summary']
        stats['collection_status'] = collection_status
        return jsonify(stats)

    data = raw if isinstance(raw, list) else []
    stats = {
        "total_items": len(data),
        "by_platform": {},
        "by_keyword": {},
        "video_count": 0,
        "top_content": [],
        "collection_status": collection_status
    }
    for item in data:
        platform = item.get('platform', 'unknown')
        keyword = item.get('keyword', 'unknown')
        stats["by_platform"][platform] = stats["by_platform"].get(platform, 0) + 1
        stats["by_keyword"][keyword] = stats["by_keyword"].get(keyword, 0) + 1
        if item.get('is_video'):
            stats["video_count"] += 1

    sorted_data = sorted(data, key=lambda x: x.get('likes', 0) or x.get('upvotes', 0), reverse=True)[:10]
    stats["top_content"] = sorted_data
    return jsonify(stats)


@app.route('/api/status')
def get_status():
    """获取收集状态"""
    return jsonify(collection_status)


@app.route('/api/deep_search', methods=['GET', 'POST'])
def deep_search_api():
    """多平台发散搜索接口"""
    if request.method == 'POST':
        body = request.get_json() or {}
    else:
        body = request.args

    keyword = body.get('keyword', '')
    keyword_en = body.get('keyword_en', '')
    fofa_query = body.get('fofa_query', '')
    platforms = body.get('platforms', None)
    limit = int(body.get('limit', 10))

    if not keyword:
        return jsonify({"error": "keyword is required"})

    try:
        from deep_searcher import deep_search
        result = asyncio.run(deep_search(
            keyword=keyword,
            keyword_en=keyword_en or None,
            fofa_query=fofa_query or None,
            platforms=platforms or None,
            limit=limit
        ))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})
def trigger_collection():
    """手动触发收集（立即在后台启动，不阻塞请求）"""
    if collection_status["running"]:
        return jsonify({"status": "already_running", "message": "收集正在进行中"})

    t = threading.Thread(target=run_collection, daemon=True)
    t.start()
    return jsonify({"status": "started", "message": "收集已在后台启动"})


if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60

    print(f"🚀 启动跨境电商情报仪表板...")
    print(f"📊 访问地址: http://localhost:{port}")

    # 启动后台自动收集（use_reloader=False 防止 debug 模式下启动两次）
    start_background_collector(interval_minutes=interval)

    app.run(host='0.0.0.0', port=port, debug=False)
