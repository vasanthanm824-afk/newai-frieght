#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# deploy.sh — Unix/Linux Automated Production Deployment Script
# ---------------------------------------------------------------------------
set -e

echo "=========================================================="
echo "  Freight Forecasting Decision Center — Automated Deploy"
echo "=========================================================="

echo -e "\n[1/3] Executing Backend Integration Test Suite..."
python3 -u test_new_backend.py
echo "✅ Backend tests passed cleanly!"

if command -v docker &> /dev/null; then
    echo -e "\n[2/3] Building and launching Docker Compose multi-container stack..."
    docker compose up --build -d
    echo -e "\n🎉 Docker Container Stack Successfully Deployed!"
    echo "   Frontend UI:  http://localhost:8501"
    echo "   FastAPI API:  http://localhost:8000"
    echo "   API Docs:     http://localhost:8000/docs"
else
    echo -e "\n[2/3] Docker not found. Starting local background services..."
    nohup uvicorn backend.main:app --host 127.0.0.1 --port 8000 > backend.log 2>&1 &
    nohup streamlit run app.py --server.port 8501 --server.headless true > frontend.log 2>&1 &
    echo -e "\n🎉 Local Production Services Successfully Deployed!"
    echo "   Frontend UI:  http://localhost:8501"
    echo "   FastAPI API:  http://localhost:8000"
fi
