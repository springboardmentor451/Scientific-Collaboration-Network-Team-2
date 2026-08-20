# run_local.ps1
# Script to run the Scientific Collaboration Network Analyzer locally with SQLite and Virtual Environment

Write-Host "Starting Scientific Collaboration Network Analyzer..." -ForegroundColor Cyan

# Set environment variables in the current session
$env:DATABASE_URL = "sqlite:///./scna.db"
$env:BACKEND_URL = "http://localhost:8000/api/v1"

# 0. Initialize Database Tables if needed
Write-Host "Verifying database tables & superuser..." -ForegroundColor Yellow
& ".\venv\Scripts\python.exe" -c "from backend.app.db.session import SessionLocal, engine; from backend.app.db.base import Base; from backend.app.db.init_db import init_db; Base.metadata.create_all(bind=engine); db = SessionLocal(); init_db(db)"

# 1. Start FastAPI Backend in a new window
Write-Host "Launching Backend on http://localhost:8000..." -ForegroundColor Green
Start-Process -FilePath ".\venv\Scripts\python.exe" -ArgumentList "-m", "uvicorn", "backend.app.main:app", "--port", "8000", "--reload" -NoNewWindow:$false

# Wait a short moment for backend to initialize
Start-Sleep -Seconds 3

# 2. Start Flask Frontend in a new window
Write-Host "Launching Frontend on http://localhost:5000..." -ForegroundColor Green
Start-Process -FilePath ".\venv\Scripts\python.exe" -ArgumentList "frontend/app.py" -NoNewWindow:$false

Write-Host "Both services launched in separate windows!" -ForegroundColor Yellow
Write-Host "- Backend API Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "- Frontend Web Portal: http://localhost:5000" -ForegroundColor Yellow
