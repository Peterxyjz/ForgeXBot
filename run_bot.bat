@echo off
echo =====================================
echo   ForgeX Bot v0.0.2
echo =====================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.8-3.11
    pause
    exit /b 1
)

REM Create venv if needed
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Checking dependencies...
pip install -r requirements.txt --quiet

REM Run bot
echo.
echo Starting ForgeX Bot...
echo Press Ctrl+C to stop
echo.
python main.py %*

REM Cleanup
deactivate
pause
