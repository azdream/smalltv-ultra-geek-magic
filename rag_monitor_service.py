import time
import datetime
import psutil
import subprocess
import requests
import io
import os
from rag_renderer import RagMonitorRenderer

SMALLTV_IP = "10.100.1.145"

# 모니터링할 미니 PC의 도커 컨테이너 이름 (부분 일치로도 동작)
TARGET_SERVICES = [
    "rag-database",   # 예: PostgreSQL, ChromaDB 등
    "rag-api-server", # 예: FastAPI 백엔드
    "ollama-llm",     # 예: 로컬 LLM
    "redis-cache"     # 예: 캐시
]

def check_docker_services():
    services_status = {svc: False for svc in TARGET_SERVICES}
    try:
        # 실행 중인 도커 컨테이너의 이름 목록을 가져옴
        output = subprocess.check_output(["docker", "ps", "--format", "{{.Names}}"], text=True)
        running_containers = output.strip().split("\n")
        
        for svc in TARGET_SERVICES:
            # 컨테이너 이름에 svc 문자열이 포함되어 있으면 실행 중으로 간주
            if any(svc in container for container in running_containers):
                services_status[svc] = True
    except Exception as e:
        # 도커가 설치되어 있지 않거나 권한이 없는 경우
        pass
    
    return services_status

def is_processing_active():
    # RAG 머신이 현재 텍스트나 데이터를 처리하고 있는지(작업 중인지) 추론
    # 예시: CPU 사용량이 30% 이상일 때 '처리 중'으로 간주
    return psutil.cpu_percent() > 30.0

def main():
    print("=" * 50)
    print("🧠 RAG Ontology Machine Monitor for SmallTV")
    print(f"🎯 Target IP: {SMALLTV_IP}")
    print("=" * 50)
    
    # 폰트 경로 설정
    fonts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    renderer = RagMonitorRenderer(fonts_dir=fonts_dir)
    
    # 초기 CPU 측정값 무시용 (첫 호출 시 0.0 반환 방지)
    psutil.cpu_percent()
    time.sleep(0.5)
    
    while True:
        try:
            now_dt = datetime.datetime.now()
            
            # 1. 시스템 정보 수집 (CPU, RAM)
            cpu_pct = psutil.cpu_percent(interval=None)
            ram_pct = psutil.virtual_memory().percent
            sys_info = {"cpu": cpu_pct, "ram": ram_pct}
            
            # 2. 도커 서비스 상태 확인
            services = check_docker_services()
            
            # 3. 작업 중 여부 확인
            processing = is_processing_active()
            
            print(f"[{now_dt.strftime('%H:%M:%S')}] CPU: {cpu_pct:04.1f}% | RAM: {ram_pct:04.1f}% | Processing: {processing}")
            
            # 4. GIF 프레임 렌더링
            gif_bytes = renderer.render_dashboard(sys_info, services, is_processing=processing, num_frames=4)
            
            # 5. SmallTV 기기로 전송 (업로드 후 적용)
            files = {'file': ('rag.gif', io.BytesIO(gif_bytes), 'image/gif')}
            res = requests.post(f"http://{SMALLTV_IP}/doUpload?dir=/image/", files=files, timeout=10)
            
            if res.status_code == 200:
                requests.get(f"http://{SMALLTV_IP}/set?img=%2Fimage%2Frag.gif", timeout=5)
            else:
                print("[!] HTTP Push Failed:", res.status_code)
                
            time.sleep(2) # 2초마다 화면 갱신
            
        except Exception as e:
            print("[!] Loop Error:", e)
            time.sleep(5)

if __name__ == "__main__":
    main()
