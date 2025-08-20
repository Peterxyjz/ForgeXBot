@echo off
echo =====================================
echo   MT5 Price Action Bot - Windows
echo =====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created.
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if requirements are installed
pip show MetaTrader5 >nul 2>&1
if errorlevel 1 (
    echo Installing requirements...
    pip install -r requirements.txt
    echo.
)

REM Run the bot
echo Starting MT5 Price Action Bot...
echo Press Ctrl+C to stop the bot
echo.
python main.py %*

REM Deactivate virtual environment
deactivate

echo.
echo Bot stopped.
pause
