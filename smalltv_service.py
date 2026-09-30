import datetime
import io
import json
import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from renderer import RetroDashboardRenderer

SMALLTV_IP = "10.100.1.145"
HTTP_PORT = 8765

# Shared App State
class AppState:
    def __init__(self):
        self.lock = threading.Lock()
        self.state_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pomo_counter.json")
        
        # Work Countdown config
        self.work_start = "08:30"
        self.work_end = "17:30"
        
        # Pomodoro Task Counter (12 tasks target)
        self.pomo_target = 12
        self.pomo_completed = 0
        self.last_task_ts = time.time()
        self.idle_decrement_interval = 1800  # 30 minutes of inactivity
        
        # Notification / Agent Hook state
        self.notify_active = False
        self.notify_until = 0
        self.notify_title = "TASK COMPLETE!"
        self.notify_message = "에이전트 작업 완료!"
        self.notify_app = "AI"

        # Device push config
        self.push_enabled = True
        self.push_interval = 5.0
        self.last_push_time = 0
        self.last_push_status = "Not started"
        
        # Weather cache
        self.weather_temp = "20"
        self.weather_desc = "Clear"
        
        # Current rendered GIF bytes
        self.current_frame_bytes = None
        
        self.load_state()

    def load_state(self):
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                today_str = datetime.date.today().isoformat()
                if data.get("date") == today_str:
                    self.pomo_completed = int(data.get("completed", 0))
                else:
                    self.pomo_completed = 0  # Reset on new day
                self.pomo_target = int(data.get("target", 12))
                self.work_start = data.get("work_start", "08:30")
                self.work_end = data.get("work_end", "17:30")
        except Exception as e:
            print("[!] Error loading state:", e)

    def save_state(self):
        try:
            data = {
                "date": datetime.date.today().isoformat(),
                "completed": self.pomo_completed,
                "target": self.pomo_target,
                "work_start": self.work_start,
                "work_end": self.work_end
            }
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("[!] Error saving state:", e)

    def trigger_notification(self, title="TASK COMPLETE!", message="에이전트 작업 완료!", duration=15, app="AI"):
        with self.lock:
            self.notify_active = True
            self.notify_title = title
            self.notify_message = message
            self.notify_app = app
            self.notify_until = time.time() + duration

    def increment_task(self, app="AI", title=None, message=None, force=False):
        with self.lock:
            now = time.time()
            # 5-second debounce against duplicate hook triggers
            if not force and (now - self.last_task_ts < 5.0):
                return self.pomo_completed
                
            self.last_task_ts = now
            
            if self.pomo_completed >= self.pomo_target:
                self.pomo_completed = 0
                
            self.pomo_completed += 1
            self.notify_app = app
            self.save_state()
            
            c = self.pomo_completed
            target = self.pomo_target
            
            if c == 1:
                t = "★ QUEST STARTED! (1/12)"
                m = "새 세션 시작! 오늘도 힘내보자구~ ★"
                dur = 25
            elif c == target:
                t = "★ 12 TASKS DONE!"
                m = "12개 완료! 이제 푹 쉬어요~"
                dur = 30
            else:
                t = title or f"[{app}] #{c} COMPLETE!"
                m = message or f"{c}/{target} 완료! (휴식까지 {target - c}개 남음) ★"
                dur = 25
                
            self.notify_active = True
            self.notify_title = t
            self.notify_message = m
            self.notify_until = now + dur
            return c

    def decrement_task(self):
        with self.lock:
            self.pomo_completed = max(0, self.pomo_completed - 1)
            self.save_state()
            return self.pomo_completed

    def reset_counter(self):
        with self.lock:
            self.pomo_completed = 0
            self.save_state()
            return self.pomo_completed

    def check_idle_decrement(self):
        with self.lock:
            if self.pomo_completed == 0:
                return False
                
            now = time.time()
            if now - self.last_task_ts >= self.idle_decrement_interval:
                self.pomo_completed = max(0, self.pomo_completed - 1)
                self.last_task_ts = now  # Reset interval
                self.save_state()
                return True
            return False

state = AppState()

# Push loop runner with Native Animated GIF support
def background_push_loop(renderer):
    print(f"[*] Background SmallTV push loop started (Target: http://{SMALLTV_IP})")
    last_minute = -1
    last_pomo = -1
    celebration_shown = False
    
    while True:
        try:
            now = time.time()
            now_dt = datetime.datetime.now()
            
            with state.lock:
                is_notifying = (now < state.notify_until)
                notif_title = state.notify_title
                notif_msg = state.notify_message
                notif_app = getattr(state, "notify_app", "AI")
                pomo_dict = {
                    "completed": state.pomo_completed,
                    "target": state.pomo_target,
                    "idle_seconds": int(now - state.last_task_ts)
                }
                work_dict = {
                    "start": state.work_start,
                    "end": state.work_end
                }
                weather_dict = {
                    "temp": state.weather_temp,
                    "desc": state.weather_desc
                }
                current_pomo = state.pomo_completed
                push_enabled = state.push_enabled

            # ---------------------------------------------
            # Case 1: Active Celebration Notification (Task Complete Fireworks!)
            # ---------------------------------------------
            if is_notifying:
                if not celebration_shown:
                    print(f"[*] Displaying Celebration GIF for {notif_app} (Task #{current_pomo})")
                    gif_bytes = renderer.render_animated_celebration(
                        app_name=notif_app,
                        count=current_pomo,
                        title=notif_title
                    )
                    print(f"[*] Celebration GIF rendered: {len(gif_bytes)} bytes")
                    with state.lock:
                        state.current_frame_bytes = gif_bytes
                        
                    if push_enabled:
                        try:
                            files = {'file': ('cel.gif', io.BytesIO(gif_bytes), 'image/gif')}
                            res = requests.post(f"http://{SMALLTV_IP}/doUpload?dir=/image/", files=files, timeout=20)
                            if res.status_code == 200:
                                requests.get(f"http://{SMALLTV_IP}/set?img=%2Fimage%2Fcel.gif", timeout=5)
                                state.last_push_status = f"Celebration Active ({now_dt.strftime('%H:%M:%S')})"
                            else:
                                err = f"HTTP Error {res.status_code} for cel.gif: {res.text[:30]}"
                                print(f"[!] {err}")
                                state.last_push_status = err
                        except Exception as ex:
                            err = f"Push Error: {str(ex)[:30]}"
                            print(f"[!] {err}")
                            state.last_push_status = err
                            
                    celebration_shown = True
                time.sleep(0.5)
                continue

            # ---------------------------------------------
            # Case 2: Celebration expired -> Restore Dashboard
            # ---------------------------------------------
            if celebration_shown and not is_notifying:
                print("[*] Celebration expired. Restoring Dashboard GIF...")
                celebration_shown = False
                last_minute = -1
                last_pomo = -1

            # ---------------------------------------------
            # Case 3: Normal Dashboard (Live 4-frame GIF)
            # ---------------------------------------------
            
            # Auto-decrement stress if idle
            if state.check_idle_decrement():
                current_pomo = state.pomo_completed
                print(f"[*] Inactivity threshold reached. Stress reduced to {current_pomo}")

            need_push = (now_dt.minute != last_minute) or (current_pomo != last_pomo)
            
            if need_push:
                print(f"[*] Rendering new Animated Dashboard GIF (Time: {now_dt.strftime('%H:%M')}, Pomo: {current_pomo}/{state.pomo_target})")
                gif_bytes = renderer.render_animated_dashboard(
                    pomodoro_state=pomo_dict,
                    weather_info=weather_dict,
                    work_config=work_dict
                )
                with state.lock:
                    state.current_frame_bytes = gif_bytes
                    
                if push_enabled:
                    try:
                        files = {'file': ('dashboard.gif', io.BytesIO(gif_bytes), 'image/gif')}
                        res = requests.post(f"http://{SMALLTV_IP}/doUpload?dir=/image/", files=files, timeout=20)
                        if res.status_code == 200:
                            requests.get(f"http://{SMALLTV_IP}/set?img=%2Fimage%2Fdashboard.gif", timeout=5)
                            state.last_push_status = f"Success ({now_dt.strftime('%H:%M:%S')})"
                            last_minute = now_dt.minute
                            last_pomo = current_pomo
                        else:
                            state.last_push_status = f"HTTP Error {res.status_code}"
                    except Exception as ex:
                        state.last_push_status = f"Conn Error: {str(ex)[:30]}"
                        
            time.sleep(0.5)
        except Exception as e:
            print("Loop error:", e)
            time.sleep(1)

AI_HOOK_MONITOR_LEDGER = "/Users/2510-n0001/variProjects/ai-hook-monitor/.data/ledger"

def ledger_watcher_loop():
    print(f"[*] Ledger Watcher started (Watching: {AI_HOOK_MONITOR_LEDGER})")
    import glob
    current_file = None
    file_handle = None
    
    while True:
        try:
            if os.path.exists(AI_HOOK_MONITOR_LEDGER):
                files = sorted(glob.glob(os.path.join(AI_HOOK_MONITOR_LEDGER, "*.jsonl")))
                if files:
                    latest = files[-1]
                    if latest != current_file:
                        if file_handle:
                            file_handle.close()
                        current_file = latest
                        file_handle = open(current_file, "r", encoding="utf-8")
                        file_handle.seek(0, os.SEEK_END)
                        print(f"[*] Watching ledger: {current_file}")
            
            if file_handle:
                line = file_handle.readline()
                if line:
                    line = line.strip()
                    if line:
                        try:
                            ev = json.loads(line)
                            event_name = ev.get("event")
                            if event_name in ("Stop", "SubagentStop"):
                                app_name = str(ev.get("app", "AI")).upper()
                                print(f"[+] Hook Event Detected from ai-hook-monitor: {app_name} {event_name}")
                                state.increment_task(app=app_name)
                        except Exception:
                            pass
                else:
                    time.sleep(0.3)
            else:
                time.sleep(1.0)
        except Exception:
            time.sleep(1.0)

# Web controller HTTP handler
class ControllerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(self.get_html().encode("utf-8"))
        elif self.path.startswith("/api/frame.gif") or self.path.startswith("/api/frame.jpg"):
            with state.lock:
                frame_data = state.current_frame_bytes
            if frame_data:
                self.send_response(200)
                content_type = "image/gif" if self.path.startswith("/api/frame.gif") else "image/jpeg"
                self.send_header("Content-Type", content_type)
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.end_headers()
                self.wfile.write(frame_data)
            else:
                self.send_response(404)
                self.end_headers()
        elif self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            with state.lock:
                data = {
                    "work_start": state.work_start,
                    "work_end": state.work_end,
                    "pomo_completed": state.pomo_completed,
                    "pomo_target": state.pomo_target,
                    "need_break": (state.pomo_completed >= state.pomo_target),
                    "push_enabled": state.push_enabled,
                    "push_interval": state.push_interval,
                    "last_push_status": state.last_push_status,
                    "smalltv_ip": SMALLTV_IP
                }
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else ""
        try:
            req = json.loads(body) if body else {}
        except Exception:
            req = {}
            
        action = req.get("action")
        
        if self.path == "/api/notify" or action == "notify":
            title = req.get("title")
            msg = req.get("message")
            app = req.get("app", "AI")
            force = req.get("force", False)
            state.increment_task(app=app, title=title, message=msg, force=force)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok","notified":true}')
            return

        if action == "task_complete":
            state.increment_task(app="USER", force=True)
        elif action == "task_decrement":
            state.decrement_task()
        elif action == "task_reset":
            state.reset_counter()
        elif action == "set_work_hours":
            with state.lock:
                if "start" in req: state.work_start = req["start"]
                if "end" in req: state.work_end = req["end"]
                state.save_state()
        elif action == "set_push":
            with state.lock:
                if "enabled" in req: state.push_enabled = bool(req["enabled"])
                if "interval" in req: state.push_interval = max(2.0, float(req["interval"]))

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def get_html(self):
        return """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>👑 프린세스 메이커 2 - SmallTV 육성 대시보드</title>
    <style>
        :root {
            --bg: #0f0c16;
            --card-bg: #1a1426;
            --accent: #ffd24d;
            --accent-pink: #ff5983;
            --accent-gold: #e6b800;
            --accent-green: #2fe084;
            --border-gold: #b38636;
            --text: #f0eaf8;
            --text-muted: #9c8fb3;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: var(--bg); color: var(--text); padding: 24px; display: flex; justify-content: center; }
        .container { max-width: 880px; width: 100%; display: grid; grid-template-columns: 280px 1fr; gap: 24px; }
        @media (max-width: 720px) { .container { grid-template-columns: 1fr; } }
        .card { background: var(--card-bg); border-radius: 16px; padding: 20px; border: 1px solid var(--border-gold); box-shadow: 0 10px 30px rgba(0,0,0,0.5); margin-bottom: 20px; position: relative; }
        .card::before { content: ""; position: absolute; inset: 3px; border: 1px solid rgba(255,210,77,0.15); border-radius: 13px; pointer-events: none; }
        h1 { font-size: 20px; font-weight: 700; margin-bottom: 4px; color: var(--accent); display: flex; align-items: center; gap: 8px; }
        .subtitle { font-size: 13px; color: var(--text-muted); margin-bottom: 16px; line-height: 1.5; }
        h2 { font-size: 15px; font-weight: 600; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; color: #ffd24d; }
        .preview-box { text-align: center; }
        .screen-frame { width: 240px; height: 240px; border-radius: 12px; border: 4px solid var(--border-gold); box-shadow: 0 0 25px rgba(255,210,77,0.25); margin: 0 auto 12px; background: #000; overflow: hidden; }
        .screen-frame img { width: 100%; height: 100%; display: block; image-rendering: pixelated; }
        .btn-group { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
        button { background: #2c203d; color: var(--text); border: 1px solid #5a427a; padding: 10px 16px; border-radius: 10px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; flex: 1; min-width: 90px; }
        button:hover { background: #3d2d54; transform: translateY(-1px); border-color: var(--accent); }
        button.primary { background: linear-gradient(135deg, #d44068, #ff5983); color: #fff; border: none; }
        button.primary:hover { background: #ff6b93; }
        button.green { background: var(--accent-green); color: #042111; font-weight: 700; border: none; }
        button.green:hover { background: #44f095; }
        button.gold { background: linear-gradient(135deg, #cc9900, #ffcc00); color: #2a1b00; font-weight: 700; border: none; }
        button.gold:hover { background: #ffd633; }
        .status-badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; background: rgba(255,210,77,0.15); color: var(--accent); margin-bottom: 14px; border: 1px solid rgba(255,210,77,0.3); }
        .input-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; font-size: 13px; }
        input[type="time"] { background: #130f1c; border: 1px solid #4a3666; color: #fff; padding: 6px 10px; border-radius: 8px; font-size: 14px; outline: none; }
        .pomo-grid { display: flex; gap: 4px; margin: 12px 0; justify-content: center; }
        .pomo-dot { width: 16px; height: 16px; border-radius: 4px; background: #1a1324; border: 1px solid #4a3666; }
        .pomo-dot.active { background: #ff5983; border-color: #ff7d9f; box-shadow: 0 0 6px rgba(255,89,131,0.6); }
        .pomo-dot.rest { background: #ff3b30; border-color: #ff6961; box-shadow: 0 0 8px rgba(255,59,48,0.8); }
    </style>
</head>
<body>
    <div class="container">
        <!-- Left: Live Animated Preview -->
        <div>
            <div class="card preview-box">
                <h2>📺 SmallTV 실시간 화면</h2>
                <div class="screen-frame">
                    <img id="preview" src="/api/frame.gif" alt="PM2 Animated GIF Preview">
                </div>
                <div class="status-badge" id="push-status">연결 확인 중...</div>
                <div style="font-size:11px; color:#9c8fb3; line-height:1.4;">
                    👑 <b>프린세스 메이커 2 육성 엔진</b><br>
                    기기 RAM에서 300ms 루프로 무한 재생 중
                </div>
                <div class="btn-group" style="margin-top:14px;">
                    <button onclick="refreshPreview()">화면 새로고침</button>
                    <button class="gold" onclick="sendTestHook()">작업 완료 알림 테스트 🎉</button>
                </div>
            </div>
        </div>

        <!-- Right: Status & Parameters -->
        <div>
            <div class="card">
                <h1>👑 트램의 일과 & 스트레스 관리</h1>
                <p class="subtitle">에이전트 작업을 마칠 때마다 태스크 카운터가 누적됩니다. 12회 완료 시 스트레스가 한계에 도달하여 휴식을 권장합니다.</p>
                
                <div style="text-align:center; margin: 16px 0;">
                    <div style="font-size: 13px; color: var(--text-muted); margin-bottom: 2px;">스트레스(피로도)</div>
                    <span id="pomo-count" style="font-size: 42px; font-weight:800; color:var(--accent-pink);">0</span>
                    <span style="font-size: 20px; color:var(--text-muted);"> / 12</span>
                    <div id="task-badge" style="margin-top:4px; font-size:15px; font-weight:700; color:var(--accent-gold);">
                        🎯 오늘 완수한 작업: <span id="task-val">0</span>개
                    </div>
                    <div id="rest-badge" style="display:none; margin-top:6px; color:#ff4d4d; font-weight:700; font-size:14px;">
                        ♨ 피로도 12 한계치! 즉시 휴식(바캉스)이 필요합니다!
                    </div>
                </div>

                <div class="pomo-grid" id="pomo-dots"></div>

                <div class="btn-group">
                    <button class="primary" onclick="postAction('task_complete')">+1 작업 완료</button>
                    <button onclick="postAction('task_decrement')">-1 차감</button>
                    <button onclick="postAction('task_reset')">일과 초기화 (0)</button>
                </div>
            </div>

            <div class="card">
                <h2>⏰ 일과 시간표 (08:30 ~ 17:30)</h2>
                <div class="input-row">
                    <label>일과 시작 (출근)</label>
                    <input type="time" id="work_start" value="08:30" onchange="saveWorkHours()">
                </div>
                <div class="input-row">
                    <label>일과 종료 (퇴근)</label>
                    <input type="time" id="work_end" value="17:30" onchange="saveWorkHours()">
                </div>
                <div style="margin-top: 10px; font-size: 12px; color: var(--text-muted);">
                    * 일과 종료 시간에 도달하면 트램 공주님이 자유시간 축하 대사를 들려줍니다!
                </div>
            </div>

            <div class="card">
                <h2>📜 업무 일지 (에이전트 훅 실시간 연동)</h2>
                <div style="font-size: 13px; line-height: 1.6; color: var(--text-muted);">
                    • <b>ai-hook-monitor</b>: <code style="color:var(--accent);">variProjects/ai-hook-monitor/.data/ledger</code> 감시 중<br>
                    • <b>AGY / CLAUDE / CHATGPT</b> 작업 완료 시 집사 큐브의 보고와 함께 화면 축하 팡파레 표출<br>
                    • 대상 기기: <code style="color:var(--accent);">http://""" + SMALLTV_IP + """</code>
                </div>
            </div>
        </div>
    </div>

    <script>
        function updateStatus() {
            fetch('/api/status')
                .then(r => r.json())
                .then(d => {
                    document.getElementById('pomo-count').textContent = d.pomo_completed;
                    document.getElementById('task-val').textContent = d.pomo_completed;
                    document.getElementById('push-status').textContent = '상태: ' + d.last_push_status;
                    document.getElementById('work_start').value = d.work_start;
                    document.getElementById('work_end').value = d.work_end;
                    
                    const isRest = d.pomo_completed >= d.pomo_target;
                    document.getElementById('rest-badge').style.display = isRest ? 'block' : 'none';
                    
                    const dotsCont = document.getElementById('pomo-dots');
                    dotsCont.innerHTML = '';
                    for (let i = 0; i < d.pomo_target; i++) {
                        const dot = document.createElement('div');
                        dot.className = 'pomo-dot';
                        if (i < d.pomo_completed) {
                            dot.classList.add(isRest ? 'rest' : 'active');
                        }
                        dotsCont.appendChild(dot);
                    }
                })
                .catch(() => {});
        }

        function refreshPreview() {
            document.getElementById('preview').src = '/api/frame.gif?t=' + Date.now();
        }

        function postAction(action, data = {}) {
            fetch('/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: action, ...data })
            }).then(() => {
                setTimeout(updateStatus, 300);
                setTimeout(refreshPreview, 2000);
            });
        }

        function sendTestHook() {
            fetch('/api/notify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    app: 'CLAUDE',
                    title: '작업 완료!',
                    message: '주인님! 태스크가 완료되었습니다!',
                    force: true
                })
            }).then(() => {
                setTimeout(updateStatus, 300);
                setTimeout(refreshPreview, 2000);
            });
        }

        function saveWorkHours() {
            const start = document.getElementById('work_start').value;
            const end = document.getElementById('work_end').value;
            postAction('set_work_hours', { start: start, end: end });
        }

        setInterval(updateStatus, 2000);
        setInterval(refreshPreview, 5000);
        updateStatus();
    </script>
</body>
</html>"""

def main():
    print("=" * 50)
    print("📺 SmallTV-Ultra 레트로 게이밍 대시보드 (Animated GIF Engine)")
    print(f"🌐 웹 컨트롤러: http://localhost:{HTTP_PORT}")
    print(f"🎯 대상 기기 IP: {SMALLTV_IP}")
    print("=" * 50)
    
    renderer = RetroDashboardRenderer(fonts_dir="fonts")
    
    # 1. Start SmallTV push loop thread
    push_th = threading.Thread(target=background_push_loop, args=(renderer,), daemon=True)
    push_th.start()
    
    # 2. Start AI hook monitor ledger watcher thread
    watcher_th = threading.Thread(target=ledger_watcher_loop, daemon=True)
    watcher_th.start()
    
    # 3. Start Web controller HTTP Server
    server = HTTPServer(("0.0.0.0", HTTP_PORT), ControllerHandler)
    print(f"[*] SmallTV Web Controller running at: http://localhost:{HTTP_PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping SmallTV Controller...")
        server.server_close()

if __name__ == "__main__":
    main()
