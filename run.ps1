# Local BI Boutique Assistant - PowerShell 1-Click Launcher
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   MISHIKA FASHION BOUTIQUE - LOCAL BI ASSISTANT (OFFLINE-FIRST)" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "[OK] Activating Python virtual environment (.venv)..." -ForegroundColor Green
    & .\.venv\Scripts\Activate.ps1
}

Write-Host "[OK] Launching Streamlit Executive Application..." -ForegroundColor Yellow
Write-Host ""
streamlit run app.py --server.port 8501 --theme.base "dark"
