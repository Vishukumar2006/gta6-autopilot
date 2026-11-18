"""Lightweight Responsive Web Dashboard Server (Mobile & Low-Spec PC Optimized)."""

import json
import urllib.parse
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
try:
    from http.server import ThreadingHTTPServer
except ImportError:
    from socketserver import ThreadingMixIn

    class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True

from pathlib import Path
from typing import Dict, Any, Optional
from src.config import SystemConfig, CLIPS_DIR, THUMBNAILS_DIR
from src.database import Database
from src.engine import AutopilotEngine


def get_local_ip() -> str:
    """Detect local LAN IP for mobile phone connection."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class DashboardRequestHandler(BaseHTTPRequestHandler):
    """Handles REST API endpoints and static dashboard assets with range support."""

    config: SystemConfig = None
    db: Database = None
    engine: AutopilotEngine = None

    def log_message(self, format, *args):
        """Suppress default HTTP stderr noise."""
        return

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        if path in ["/", "/index.html"]:
            self._serve_dashboard_html()
        elif path == "/api/status":
            self._serve_json(self._get_status_data())
        elif path == "/api/stats":
            self._serve_json(self.db.get_dashboard_stats())
        elif path == "/api/streams":
            self._serve_json(self.db.get_recent_streams(20))
        elif path == "/api/clips":
            self._serve_json(self.db.get_clips(50))
        elif path == "/api/publications":
            self._serve_json(self.db.get_recent_publications(50))
        elif path == "/api/logs":
            self._serve_json(self.db.get_logs(100))
        elif path.startswith("/media/clips/"):
            clip_name = path.replace("/media/clips/", "")
            safe_file = CLIPS_DIR / Path(clip_name).name
            self._serve_file(safe_file, "video/mp4")
        elif path.startswith("/media/thumbnails/"):
            thumb_name = path.replace("/media/thumbnails/", "")
            safe_file = THUMBNAILS_DIR / Path(thumb_name).name
            self._serve_file(safe_file, "image/jpeg")
        else:
            self.send_error(404, "Endpoint Not Found")

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        if path == "/api/action/run_cycle":
            try:
                result = self.engine.run_full_cycle()
                self._serve_json({"status": "success", "result": result})
            except Exception as e:
                self._serve_json({"status": "error", "message": str(e)}, status=500)

        elif path == "/api/action/toggle_autopilot":
            if self.engine.is_running:
                self.engine.stop()
            else:
                self.engine.start()
            self._serve_json({"status": "success", "running": self.engine.is_running})

        elif path == "/api/action/toggle_low_spec":
            self.config.low_spec_mode = not self.config.low_spec_mode
            self.config.save()
            self._serve_json(
                {"status": "success", "low_spec_mode": self.config.low_spec_mode}
            )

        elif path == "/api/action/settings":
            if "low_spec_mode" in payload:
                self.config.low_spec_mode = bool(payload["low_spec_mode"])
            if "dry_run" in payload:
                self.config.social.dry_run = bool(payload["dry_run"])
            self.config.save()
            self._serve_json({"status": "success", "config": self.config.to_dict()})

        else:
            self.send_error(404, "Action Not Found")

    def _serve_json(self, data: Any, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, file_path: Path, content_type: str):
        """Serve media file with HTTP 206 byte-range support for mobile Safari & Chrome."""
        safe_name = Path(file_path).name
        parent_dir = file_path.parent.resolve()
        resolved_path = (parent_dir / safe_name).resolve()

        if not resolved_path.exists() or not resolved_path.is_file():
            self.send_error(404, "File Not Found")
            return

        file_size = resolved_path.stat().st_size
        range_header = self.headers.get("Range")

        try:
            if range_header and range_header.startswith("bytes="):
                # Parse Range: bytes=start-end
                range_spec = range_header.replace("bytes=", "").strip()
                parts = range_spec.split("-")
                start = int(parts[0]) if parts[0] else 0
                end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1

                start = max(0, min(start, file_size - 1))
                end = max(start, min(end, file_size - 1))
                length = end - start + 1

                self.send_response(206)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Length", str(length))
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                with open(resolved_path, "rb") as f:
                    f.seek(start)
                    bytes_remaining = length
                    while bytes_remaining > 0:
                        chunk_size = min(65536, bytes_remaining)
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        bytes_remaining -= len(chunk)
            else:
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(file_size))
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                with open(resolved_path, "rb") as f:
                    while chunk := f.read(65536):
                        self.wfile.write(chunk)
        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
            pass

    def _serve_dashboard_html(self):
        html = get_dashboard_html(self.config, self.engine)
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _get_status_data(self) -> Dict[str, Any]:
        local_ip = get_local_ip()
        return {
            "is_running": self.engine.is_running,
            "low_spec_mode": self.config.low_spec_mode,
            "cycle_count": self.engine._cycle_count,
            "last_cycle": self.engine._last_cycle_time,
            "port": self.config.port,
            "local_ip": local_ip,
            "mobile_url": f"http://{local_ip}:{self.config.port}",
            "dry_run": self.config.social.dry_run,
        }


def get_dashboard_html(config: SystemConfig, engine: AutopilotEngine) -> str:
    """Generate modern, responsive Vice City styled HTML5/CSS3 Dashboard."""
    local_ip = get_local_ip()
    mobile_url = f"http://{local_ip}:{config.port}"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
  <title>GTA 6 Autopilot | 24/7 Shorts & Reels</title>
  <style>
    :root {{
      --bg: #0d0221;
      --card-bg: #190933;
      --card-border: #3b1d60;
      --accent-pink: #ff007f;
      --accent-cyan: #00f0ff;
      --accent-yellow: #ffe600;
      --text-main: #f0f2f5;
      --text-dim: #9aa0a6;
      --success: #00ff88;
      --danger: #ff3366;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
    body {{ background: var(--bg); color: var(--text-main); min-height: 100vh; padding-bottom: 50px; }}
    header {{
      background: linear-gradient(135deg, #1f033d 0%, #0d0221 100%);
      border-bottom: 2px solid var(--accent-pink);
      padding: 16px 20px;
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      position: sticky;
      top: 0;
      z-index: 100;
    }}
    .brand {{ display: flex; align-items: center; gap: 10px; }}
    .logo-badge {{
      background: linear-gradient(45deg, var(--accent-pink), var(--accent-cyan));
      color: #fff;
      font-weight: 900;
      font-size: 1.1rem;
      padding: 6px 12px;
      border-radius: 8px;
      letter-spacing: 1px;
    }}
    .title-group h1 {{ font-size: 1.25rem; font-weight: 800; letter-spacing: 0.5px; }}
    .title-group p {{ font-size: 0.75rem; color: var(--accent-cyan); }}
    
    .header-actions {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}
    .btn {{
      padding: 10px 14px;
      min-height: 42px;
      border-radius: 8px;
      font-size: 0.85rem;
      font-weight: 700;
      cursor: pointer;
      border: none;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      user-select: none;
    }}
    .btn-pink {{ background: var(--accent-pink); color: #fff; box-shadow: 0 0 10px rgba(255,0,127,0.4); }}
    .btn-pink:hover {{ background: #e00070; }}
    .btn-cyan {{ background: var(--accent-cyan); color: #0d0221; }}
    .btn-cyan:hover {{ background: #00c7d4; }}
    .btn-outline {{ background: transparent; border: 1px solid var(--card-border); color: var(--text-main); }}
    .btn-outline:hover {{ background: var(--card-bg); border-color: var(--accent-cyan); }}

    .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
    
    /* Metrics Grid */
    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 12px;
      margin-bottom: 20px;
    }}
    .metric-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 14px;
      text-align: center;
    }}
    .metric-val {{ font-size: 1.6rem; font-weight: 800; color: var(--accent-cyan); }}
    .metric-lbl {{ font-size: 0.75rem; color: var(--text-dim); text-transform: uppercase; margin-top: 4px; }}
    
    /* Device / Mobile Banner */
    .mobile-banner {{
      background: linear-gradient(90deg, #2b0b4a, #16082e);
      border: 1px dashed var(--accent-cyan);
      border-radius: 10px;
      padding: 12px 16px;
      margin-bottom: 20px;
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      font-size: 0.85rem;
    }}
    .mobile-banner strong {{ color: var(--accent-yellow); }}

    /* Section Tabs & Cards */
    .section-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 16px;
      margin-bottom: 20px;
    }}
    .section-title {{
      font-size: 1rem;
      font-weight: 700;
      color: var(--accent-pink);
      margin-bottom: 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    /* Gallery */
    .clip-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 14px;
    }}
    .clip-card {{
      background: #110524;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }}
    .clip-preview {{
      width: 100%;
      aspect-ratio: 9/16;
      max-height: 280px;
      background: #000;
      object-fit: cover;
    }}
    .clip-info {{ padding: 10px; flex-grow: 1; }}
    .clip-title {{ font-size: 0.8rem; font-weight: 700; color: #fff; margin-bottom: 6px; line-height: 1.2; }}
    .clip-hook {{ font-size: 0.75rem; color: var(--accent-yellow); font-weight: bold; margin-bottom: 6px; }}
    .badge {{
      display: inline-block;
      padding: 3px 8px;
      font-size: 0.65rem;
      font-weight: bold;
      border-radius: 4px;
      background: #331355;
      color: var(--accent-cyan);
    }}

    /* Tables */
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.8rem; text-align: left; }}
    th {{ background: #130429; color: var(--text-dim); padding: 10px; font-weight: 600; }}
    td {{ padding: 10px; border-bottom: 1px solid #261142; }}
    tr:hover {{ background: #200b3b; }}
    
    /* Log console */
    .log-box {{
      background: #080114;
      border: 1px solid #220b38;
      border-radius: 8px;
      padding: 10px;
      font-family: monospace;
      font-size: 0.75rem;
      max-height: 220px;
      overflow-y: auto;
      color: #39ff14;
    }}
    .log-line {{ margin-bottom: 4px; line-height: 1.4; }}
    .log-INFO {{ color: #7af; }}
    .log-WARNING {{ color: #fa0; }}
    .log-ERROR {{ color: #f55; }}

    /* Responsive Mobile Layout */
    @media (max-width: 680px) {{
      header {{ padding: 12px 14px; flex-direction: column; align-items: stretch; }}
      .header-actions {{ width: 100%; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
      .header-actions .btn {{ justify-content: center; padding: 10px 8px; font-size: 0.8rem; }}
      #specBtn {{ grid-column: span 2; }}
      .container {{ padding: 12px; }}
      .clip-grid {{ grid-template-columns: 1fr; }}
      .metrics-grid {{ grid-template-columns: repeat(2, 1fr); }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="logo-badge">GTA VI</div>
      <div class="title-group">
        <h1>AUTOPILOT PIPELINE</h1>
        <p>100% Autonomous Clipping & Cross-Poster</p>
      </div>
    </div>
    <div class="header-actions">
      <button id="toggleBtn" class="btn btn-pink" onclick="toggleAutopilot()">
        <span>⚡</span> <span id="toggleText">Start Autopilot</span>
      </button>
      <button id="runCycleBtn" class="btn btn-cyan" onclick="runCycleNow(event)">
        <span>▶</span> Run Cycle Now
      </button>
      <button id="specBtn" class="btn btn-outline" onclick="toggleLowSpec()">
        <span>💻</span> Low-Spec PC Mode: ON
      </button>
    </div>
  </header>

  <div class="container">
    <!-- Mobile Access Alert -->
    <div class="mobile-banner">
      <div>📱 <strong>Mobile Control Active:</strong> 24/7 Cloud Server at <strong id="mobileUrlDisplay">{mobile_url}</strong></div>
      <span class="badge" style="background:var(--accent-pink);color:#fff;">24/7 CLOUD ACTIVE</span>
    </div>

    <!-- Metrics -->
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-val" id="statStreams">0</div>
        <div class="metric-lbl">Streams Found</div>
      </div>
      <div class="metric-card">
        <div class="metric-val" id="statClips">0</div>
        <div class="metric-lbl">Clips Rendered</div>
      </div>
      <div class="metric-card">
        <div class="metric-val" id="statPublished" style="color:var(--success)">0</div>
        <div class="metric-lbl">Total Published</div>
      </div>
      <div class="metric-card">
        <div class="metric-val" id="statPending" style="color:var(--accent-yellow)">0</div>
        <div class="metric-lbl">Queue Pending</div>
      </div>
    </div>

    <!-- Generated Clips Gallery -->
    <div class="section-card">
      <div class="section-title">
        <span>🎬 Latest 9:16 Shorts & Reels (Ready for Viral Traffic)</span>
        <span class="badge" id="clipsBadge">0 CLIPS</span>
      </div>
      <div class="clip-grid" id="clipGrid">
        <div style="color:var(--text-dim);padding:20px;font-size:0.85rem;">No clips generated yet. Click "Run Cycle Now" to create your first clip.</div>
      </div>
    </div>

    <!-- Publications Queue -->
    <div class="section-card">
      <div class="section-title">
        <span>📤 Autonomous Cross-Posting Queue (YouTube & Instagram)</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Platform</th>
              <th>Hook / Title</th>
              <th>Status</th>
              <th>Scheduled</th>
              <th>Link</th>
            </tr>
          </thead>
          <tbody id="pubTableBody">
            <tr><td colspan="5" style="color:var(--text-dim);text-align:center;">No pending posts</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Discovered Streams -->
    <div class="section-card">
      <div class="section-title">
        <span>📡 Monitored GTA 6 Live Streams</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Title</th>
              <th>Channel</th>
              <th>Viewers</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody id="streamTableBody">
            <tr><td colspan="4" style="color:var(--text-dim);text-align:center;">No streams monitored yet</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Live Logs -->
    <div class="section-card">
      <div class="section-title">
        <span>📟 Autonomous System Logs</span>
      </div>
      <div class="log-box" id="logBox">
        <div class="log-line log-INFO">System initialized and ready for automated clipping.</div>
      </div>
    </div>
  </div>

  <script>
    function escapeHTML(str) {{
      if (!str) return '';
      return String(str).replace(/[&<>'"]/g, tag => ({{
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;'
      }}[tag] || tag));
    }}

    async function fetchJSON(url, opts) {{
      try {{
        const r = await fetch(url, opts);
        return await r.json();
      }} catch(e) {{
        return null;
      }}
    }}

    async function refreshAll() {{
      if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {{
        const mobElem = document.getElementById('mobileUrlDisplay');
        if (mobElem) mobElem.innerText = window.location.origin;
      }}
      const status = await fetchJSON('/api/status');
      if (status) {{
        document.getElementById('toggleText').innerText = status.is_running ? 'Pause Autopilot' : 'Start Autopilot';
        document.getElementById('specBtn').innerText = '💻 Low-Spec PC: ' + (status.low_spec_mode ? 'ON' : 'OFF');
      }}

      const stats = await fetchJSON('/api/stats');
      if (stats) {{
        document.getElementById('statStreams').innerText = stats.total_streams || 0;
        document.getElementById('statClips').innerText = stats.total_clips || 0;
        document.getElementById('statPublished').innerText = stats.total_published || 0;
        document.getElementById('statPending').innerText = stats.total_pending || 0;
      }}

      const clips = await fetchJSON('/api/clips');
      if (clips && clips.length > 0) {{
        document.getElementById('clipsBadge').innerText = clips.length + ' CLIPS';
        const grid = document.getElementById('clipGrid');
        grid.innerHTML = clips.map(c => `
          <div class="clip-card">
            <video class="clip-preview" controls preload="metadata" playsinline poster="/media/thumbnails/${{c.clip_id}}.jpg">
              <source src="/media/clips/${{c.clip_id}}.mp4" type="video/mp4">
            </video>
            <div class="clip-info">
              <div class="clip-hook">${{escapeHTML(c.hook_text)}}</div>
              <div class="clip-title">${{escapeHTML(c.title)}}</div>
              <div style="display:flex;justify-content:space-between;margin-top:8px;">
                <span class="badge">🔥 ${{c.excitement_score}}/10</span>
                <span class="badge">${{Math.round(c.duration)}}s</span>
              </div>
            </div>
          </div>
        `).join('');
      }}

      const pubs = await fetchJSON('/api/publications');
      if (pubs && pubs.length > 0) {{
        const tbody = document.getElementById('pubTableBody');
        tbody.innerHTML = pubs.map(p => `
          <tr>
            <td><strong>${{escapeHTML(p.platform.toUpperCase())}}</strong></td>
            <td>${{escapeHTML(p.title)}}</td>
            <td><span class="badge" style="background:${{p.status === 'PUBLISHED' ? '#00ff8822;color:#00ff88' : '#ffaa0022;color:#ffaa00'}}">${{p.status}}</span></td>
            <td>${{p.scheduled_at ? p.scheduled_at.split('T')[1].split('.')[0] : '-'}}</td>
            <td>${{p.remote_url ? `<a href="${{escapeHTML(p.remote_url)}}" target="_blank" style="color:var(--accent-cyan)">View Post</a>` : '-'}}</td>
          </tr>
        `).join('');
      }}

      const streams = await fetchJSON('/api/streams');
      if (streams && streams.length > 0) {{
        const sbody = document.getElementById('streamTableBody');
        sbody.innerHTML = streams.map(s => `
          <tr>
            <td><strong>${{escapeHTML(s.title)}}</strong></td>
            <td>${{escapeHTML(s.channel_name)}}</td>
            <td>${{s.view_count.toLocaleString()}}</td>
            <td><span class="badge">${{escapeHTML(s.status)}}</span></td>
          </tr>
        `).join('');
      }}

      const logs = await fetchJSON('/api/logs');
      if (logs && logs.length > 0) {{
        const logBox = document.getElementById('logBox');
        logBox.innerHTML = logs.map(l => `
          <div class="log-line log-${{escapeHTML(l.level)}}">[${{l.timestamp ? l.timestamp.split('T')[1].split('.')[0] : ''}}] [${{escapeHTML(l.module)}}] ${{escapeHTML(l.message)}}</div>
        `).join('');
      }}
    }}

    async function toggleAutopilot() {{
      await fetchJSON('/api/action/toggle_autopilot', {{ method: 'POST' }});
      refreshAll();
    }}

    async function runCycleNow(evt) {{
      const btn = (evt && evt.target) ? evt.target.closest('button') : document.getElementById('runCycleBtn');
      if (btn) {{
        btn.disabled = true;
        btn.innerHTML = '<span>⏳</span> Processing...';
      }}
      try {{
        await fetchJSON('/api/action/run_cycle', {{ method: 'POST' }});
      }} finally {{
        if (btn) {{
          btn.disabled = false;
          btn.innerHTML = '<span>▶</span> Run Cycle Now';
        }}
        refreshAll();
      }}
    }}

    async function toggleLowSpec() {{
      await fetchJSON('/api/action/toggle_low_spec', {{ method: 'POST' }});
      refreshAll();
    }}

    setInterval(refreshAll, 3000);
    refreshAll();
  </script>
</body>
</html>
"""


def run_dashboard_server(
    config: Optional[SystemConfig] = None,
    engine: Optional[AutopilotEngine] = None,
    db: Optional[Database] = None,
    block: bool = True,
) -> ThreadingHTTPServer:
    """Launch the Dashboard HTTP server."""
    cfg = config or SystemConfig.load()
    eng = engine or AutopilotEngine(cfg, db)
    database = db or Database()

    DashboardRequestHandler.config = cfg
    DashboardRequestHandler.engine = eng
    DashboardRequestHandler.db = database

    server = ThreadingHTTPServer((cfg.host, cfg.port), DashboardRequestHandler)
    server.daemon_threads = True
    eng.db.log(
        "INFO",
        "Dashboard",
        f"Server running at http://{cfg.host}:{cfg.port} (Mobile: http://{get_local_ip()}:{cfg.port})",
    )

    if block:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.server_close()
    else:
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
    return server
