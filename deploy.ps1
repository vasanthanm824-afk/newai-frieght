# ---------------------------------------------------------------------------
# deploy.ps1 — Windows PowerShell One-Command Deployment Script
# ---------------------------------------------------------------------------
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Freight Forecasting Decision Center -- Automated Deploy" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

Write-Host "[1/3] Executing Backend Integration Test Suite..." -ForegroundColor Yellow
& .venv\Scripts\python.exe -u test_new_backend.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Backend tests failed. Aborting deployment." -ForegroundColor Red
    exit 1
}
Write-Host "SUCCESS: Backend tests passed cleanly!" -ForegroundColor Green

Write-Host "[2/3] Checking Docker installation..." -ForegroundColor Yellow
$dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerInstalled) {
    Write-Host "Docker detected. Building and launching containers via Docker Compose..." -ForegroundColor Cyan
    docker compose up --build -d
    Write-Host "Deployment Complete!" -ForegroundColor Green
    Write-Host "   Frontend Decision Center UI: http://localhost:8501" -ForegroundColor Green
    Write-Host "   FastAPI REST Backend Server: http://localhost:8000" -ForegroundColor Green
    Write-Host "   Interactive API Docs:        http://localhost:8000/docs" -ForegroundColor Green
} else {
    Write-Host "Docker command not found. Starting local background services directly..." -ForegroundColor Yellow
    
    Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "-m uvicorn backend.main:app --host 127.0.0.1 --port 8000" -WindowStyle Hidden
    Write-Host "  FastAPI Backend launched on http://127.0.0.1:8000" -ForegroundColor Green

    Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "-m streamlit run app.py --server.port 8501 --server.headless true" -WindowStyle Hidden
    Write-Host "  Streamlit Frontend UI launched on http://localhost:8501" -ForegroundColor Green

    Write-Host "Local Production Deployment Complete!" -ForegroundColor Green
}
