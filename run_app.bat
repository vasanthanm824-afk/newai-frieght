@echo off
title SmartVesselAI Working Model Launcher
cd /d "%~dp0"
echo ==========================================================
echo   SmartVessel AI - Application Launcher
echo ==========================================================
if not exist ".venv\Scripts\python.exe" (
    echo [SETUP] Creating Python virtual environment...
    py -3.11 -m venv .venv || python -m venv .venv
    echo [SETUP] Installing required dependencies...
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt streamlit plotly xgboost matplotlib lxml
)
echo [START] Launching SmartVessel AI Application...
.\.venv\Scripts\python.exe run_app.py
pause
