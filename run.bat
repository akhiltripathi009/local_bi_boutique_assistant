@echo off
title Local BI Boutique Assistant
echo ================================================================
echo    MISHIKA FASHION BOUTIQUE - LOCAL BI ASSISTANT (OFFLINE-FIRST)
echo ================================================================
echo.

REM Automatically activate virtual environment if detected
if exist .venv\Scripts\activate.bat (
    echo [OK] Activating Python virtual environment (.venv)...
    call .venv\Scripts\activate.bat
) else if exist env\Scripts\activate.bat (
    echo [OK] Activating Python virtual environment (env)...
    call env\Scripts\activate.bat
)

echo [OK] Launching Streamlit Executive Application...
echo.
streamlit run app.py --server.port 8501 --theme.base "dark"
pause
