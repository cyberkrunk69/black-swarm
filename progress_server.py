#!/usr/bin/env python3
"""
Live progress dashboard with real-time Server-Sent Events.
Simple, reliable, and actually works.

Usage:
    py progress_server.py          # Local only on port 8080
    py progress_server.py --lan    # LAN accessible
"""

import http.server
import socketserver
import argparse
import json
import threading
import time
import os
from pathlib import Path
from datetime import datetime

PORT = 8080
WORKSPACE = Path(__file__).parent

# Global: list of SSE client queues and file modification times
sse_clients = []
sse_lock = threading.Lock()
last_mtimes = {}


def get_file_mtimes():
    """Get modification times of monitored files."""
    files = [
        WORKSPACE / "wave_status.json",
        WORKSPACE / "SUMMARY.md",
        WORKSPACE / "PROGRESS.md",
        WORKSPACE / "learned_lessons.json",
    ]
    mtimes = {}
    for f in files:
        try:
            if f.exists():
                mtimes[str(f)] = f.stat().st_mtime
        except:
            pass
    return mtimes


def load_wave_status():
    """Load wave status from JSON."""
    wave_file = WORKSPACE / "wave_status.json"
    if wave_file.exists():
        try:
            return json.loads(wave_file.read_text(encoding='utf-8'))
        except:
            pass
    return {"waves": [], "current_activity": {"title": "Loading...", "workers": []}}


def get_stats():
    """Get basic stats."""
    logs_dir = WORKSPACE / "grind_logs"
    sessions = len(list(logs_dir.glob("*.json"))) if logs_dir.exists() else 0

    lessons = 0
    lessons_file = WORKSPACE / "learned_lessons.json"
    if lessons_file.exists():
        try:
            data = json.loads(lessons_file.read_text(encoding='utf-8'))
            if isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, list):
                        lessons += len(v)
            elif isinstance(data, list):
                lessons = len(data)
        except:
            pass

    py_files = set(WORKSPACE.glob("*.py")) | set(WORKSPACE.glob("**/*.py"))
    files = len(py_files)
    lines = sum(len(f.read_text(encoding='utf-8', errors='ignore').splitlines()) for f in py_files if f.exists())

    return {"sessions": sessions, "lessons": lessons, "files": files, "lines": lines}


def get_dashboard_data():
    """Get all data needed for dashboard as JSON."""
    wave_data = load_wave_status()
    stats = get_stats()
    return {
        "waves": wave_data.get("waves", []),
        "current_activity": wave_data.get("current_activity", {}),
        "stats": stats,
        "timestamp": datetime.now().strftime('%H:%M:%S')
    }


def broadcast_update():
    """Send update to all SSE clients."""
    data = json.dumps(get_dashboard_data())
    message = f"data: {data}\n\n"

    with sse_lock:
        dead_clients = []
        for client in sse_clients:
            try:
                client['wfile'].write(message.encode('utf-8'))
                client['wfile'].flush()
            except:
                dead_clients.append(client)
        for c in dead_clients:
            sse_clients.remove(c)


def file_watcher():
    """Watch files and broadcast on changes."""
    global last_mtimes
    last_mtimes = get_file_mtimes()

    while True:
        time.sleep(1)
        current = get_file_mtimes()
        if current != last_mtimes:
            last_mtimes = current
            broadcast_update()


def get_dashboard_html():
    """Single-page dashboard with SSE auto-refresh."""
    data = get_dashboard_data()
    waves = data["waves"]
    activity = data["current_activity"]
    stats = data["stats"]

    # Build wave tracker HTML
    wave_html = ""
    for w in waves:
        status = w.get("status", "planned")
        if status == "done":
            cls, icon = "done", "✓"
        elif status == "running":
            cls, icon = "running", "⚡"
        else:
            cls, icon = "planned", "○"

        wave_html += f'''<div class="wave {cls}">
            <span class="icon">{icon}</span>
            <span class="num">Wave {w["num"]}</span>
            <span class="name">{w["name"]}</span>
        </div>'''

    # Build workers HTML
    workers_html = ""
    for w in activity.get("workers", []):
        workers_html += f'''<div class="worker">
            <div class="type">{w.get("type", "Worker")}</div>
            <div class="task">{w.get("task", "Working...")}</div>
        </div>'''

    return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AI Progress Dashboard</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d1117;
            color: #e6edf3;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}

        header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        h1 {{
            color: #58a6ff;
            font-size: 1.8em;
            margin-bottom: 5px;
        }}
        .subtitle {{ color: #7ee787; font-size: 1em; }}

        .status-badge {{
            position: fixed;
            top: 15px;
            right: 15px;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 500;
        }}
        .status-badge.live {{ background: #238636; color: white; }}
        .status-badge.offline {{ background: #da3633; color: white; }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 25px;
        }}
        @media (max-width: 600px) {{
            .stats {{ grid-template-columns: repeat(2, 1fr); }}
        }}
        .stat {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }}
        .stat .value {{
            font-size: 2em;
            font-weight: bold;
            color: #58a6ff;
        }}
        .stat .label {{
            color: #8b949e;
            font-size: 0.85em;
            margin-top: 4px;
        }}

        .section {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .section-title {{
            color: #7ee787;
            font-size: 1.1em;
            margin-bottom: 15px;
        }}

        .wave-tracker {{
            display: flex;
            gap: 8px;
            overflow-x: auto;
            padding: 5px 0;
        }}
        .wave {{
            flex-shrink: 0;
            padding: 10px 14px;
            border-radius: 8px;
            text-align: center;
            font-size: 0.85em;
        }}
        .wave.done {{
            background: linear-gradient(135deg, #238636, #2ea043);
            color: white;
        }}
        .wave.running {{
            background: linear-gradient(135deg, #1f6feb, #58a6ff);
            color: white;
            animation: pulse 2s infinite;
        }}
        .wave.planned {{
            background: #21262d;
            color: #8b949e;
            border: 1px dashed #30363d;
        }}
        @keyframes pulse {{
            0%, 100% {{ box-shadow: 0 0 0 0 rgba(88,166,255,0.4); }}
            50% {{ box-shadow: 0 0 15px 5px rgba(88,166,255,0.2); }}
        }}
        .wave .icon {{ margin-right: 4px; }}
        .wave .name {{ display: block; font-size: 0.8em; margin-top: 3px; opacity: 0.9; }}

        .activity {{
            background: rgba(31, 111, 235, 0.1);
            border: 1px solid #1f6feb;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .activity-title {{
            color: #58a6ff;
            font-size: 1.1em;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .activity-title::before {{
            content: '';
            width: 10px;
            height: 10px;
            background: #58a6ff;
            border-radius: 50%;
            animation: blink 1s infinite;
        }}
        @keyframes blink {{
            50% {{ opacity: 0.3; }}
        }}
        .workers {{
            display: grid;
            gap: 10px;
        }}
        .worker {{
            background: #0d1117;
            padding: 12px;
            border-radius: 8px;
        }}
        .worker .type {{
            color: #d2a8ff;
            font-weight: 600;
            margin-bottom: 4px;
        }}
        .worker .task {{
            color: #8b949e;
            font-size: 0.9em;
        }}

        .timestamp {{
            text-align: center;
            color: #484f58;
            font-size: 0.8em;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="status-badge live" id="status">● Live</div>

    <div class="container">
        <header>
            <h1>AI Self-Improvement</h1>
            <div class="subtitle">Autonomous learning in progress</div>
        </header>

        <div class="stats" id="stats">
            <div class="stat"><div class="value" id="stat-sessions">{stats['sessions']}</div><div class="label">Sessions</div></div>
            <div class="stat"><div class="value" id="stat-lessons">{stats['lessons']}</div><div class="label">Lessons</div></div>
            <div class="stat"><div class="value" id="stat-files">{stats['files']}</div><div class="label">Files</div></div>
            <div class="stat"><div class="value" id="stat-lines">{stats['lines']:,}</div><div class="label">Lines</div></div>
        </div>

        <div class="section">
            <div class="section-title">Wave Progress</div>
            <div class="wave-tracker" id="waves">{wave_html}</div>
        </div>

        <div class="activity" id="activity">
            <div class="activity-title" id="activity-title">{activity.get('title', 'Idle')}</div>
            <div class="workers" id="workers">{workers_html if workers_html else '<div class="worker"><div class="task">No active workers</div></div>'}</div>
        </div>

        <div class="timestamp" id="timestamp">Updated: {data['timestamp']}</div>
    </div>

    <script>
        function updateDashboard(data) {{
            // Update stats
            document.getElementById('stat-sessions').textContent = data.stats.sessions;
            document.getElementById('stat-lessons').textContent = data.stats.lessons;
            document.getElementById('stat-files').textContent = data.stats.files;
            document.getElementById('stat-lines').textContent = data.stats.lines.toLocaleString();

            // Update waves
            let wavesHtml = '';
            data.waves.forEach(w => {{
                let cls = w.status === 'done' ? 'done' : (w.status === 'running' ? 'running' : 'planned');
                let icon = w.status === 'done' ? '✓' : (w.status === 'running' ? '⚡' : '○');
                wavesHtml += `<div class="wave ${{cls}}"><span class="icon">${{icon}}</span><span class="num">Wave ${{w.num}}</span><span class="name">${{w.name}}</span></div>`;
            }});
            document.getElementById('waves').innerHTML = wavesHtml;

            // Update activity
            document.getElementById('activity-title').innerHTML = data.current_activity.title || 'Idle';
            let workersHtml = '';
            (data.current_activity.workers || []).forEach(w => {{
                workersHtml += `<div class="worker"><div class="type">${{w.type || 'Worker'}}</div><div class="task">${{w.task || 'Working...'}}</div></div>`;
            }});
            document.getElementById('workers').innerHTML = workersHtml || '<div class="worker"><div class="task">No active workers</div></div>';

            // Update timestamp
            document.getElementById('timestamp').textContent = 'Updated: ' + data.timestamp;
        }}

        function connect() {{
            const status = document.getElementById('status');
            const es = new EventSource('/events');

            es.onopen = () => {{
                status.className = 'status-badge live';
                status.textContent = '● Live';
            }};

            es.onmessage = (e) => {{
                try {{
                    updateDashboard(JSON.parse(e.data));
                }} catch(err) {{
                    console.error('Parse error:', err);
                }}
            }};

            es.onerror = () => {{
                status.className = 'status-badge offline';
                status.textContent = '● Reconnecting...';
                es.close();
                setTimeout(connect, 3000);
            }};
        }}

        connect();
    </script>
</body>
</html>'''


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/', '/index.html', '/dad', '/summary'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(get_dashboard_html().encode('utf-8'))

        elif self.path == '/events':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()

            client = {'wfile': self.wfile}
            with sse_lock:
                sse_clients.append(client)

            # Send initial data
            try:
                data = json.dumps(get_dashboard_data())
                self.wfile.write(f"data: {data}\n\n".encode('utf-8'))
                self.wfile.flush()

                # Keep connection alive
                while True:
                    time.sleep(30)
                    self.wfile.write(": keepalive\n\n".encode('utf-8'))
                    self.wfile.flush()
            except:
                pass
            finally:
                with sse_lock:
                    if client in sse_clients:
                        sse_clients.remove(client)

        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_dashboard_data()).encode('utf-8'))

        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass  # Suppress logs


class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


def get_local_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"


def main():
    parser = argparse.ArgumentParser(description="Live progress dashboard")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--lan", action="store_true", help="LAN accessible")
    args = parser.parse_args()

    # Start file watcher
    threading.Thread(target=file_watcher, daemon=True).start()

    host = "0.0.0.0" if args.lan else ""

    with ThreadedServer((host, args.port), Handler) as server:
        print(f"Dashboard: http://localhost:{args.port}")
        if args.lan:
            print(f"LAN:       http://{get_local_ip()}:{args.port}")
        print("Live updates enabled. Ctrl+C to stop.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
