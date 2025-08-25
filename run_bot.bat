@echo off
echo =====================================
echo   ForgeX Bot v0.0.2
echo =====================================

REM Check if .env exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please run setup.bat first or copy .env.example to .env
    pause
    exit /b 1
)

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Check virtual environment
if not exist "venv" (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start bot
echo.
echo Starting ForgeX Bot...
echo Press Ctrl+C to stop
echo.
python main.py %*

REM Cleanup
deactivate
if not "%1"=="--test" pause
