#!/bin/bash
# SmallTV-Ultra 커스텀 데스크 모니터 서비스 실행 스크립트

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install pillow psutil requests
fi

echo "=================================================="
echo "📺 SmallTV-Ultra 레트로 게이밍 대시보드 시작"
echo "🌐 웹 컨트롤러: http://localhost:8765"
echo "🎯 대상 기기 IP: 10.100.1.145"
echo "=================================================="

exec .venv/bin/python3 smalltv_service.py
