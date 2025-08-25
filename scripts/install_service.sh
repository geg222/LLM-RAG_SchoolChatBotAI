#!/bin/bash

# 한성대학교 챗봇 시스템 서비스 설치 스크립트

SERVICE_NAME="hansung-chatbot"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_PATH=$(which python3)

echo "🚀 한성대학교 챗봇 시스템 서비스 설치"
echo "📁 프로젝트 디렉토리: $PROJECT_DIR"
echo "🐍 Python 경로: $PYTHON_PATH"

# 서비스 파일 생성
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Hansung University Chatbot Service
After=network.target mysql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PYTHON_PATH -m uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "서비스 파일이 생성되었습니다: $SERVICE_FILE"

# 서비스 활성화
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo "서비스가 설치되고 시작되었습니다."
echo "서비스 상태 확인: sudo systemctl status $SERVICE_NAME"
echo "서비스 재시작: sudo systemctl restart $SERVICE_NAME"
echo "서비스 중지: sudo systemctl stop $SERVICE_NAME" 