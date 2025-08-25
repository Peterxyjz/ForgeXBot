@echo off
echo =====================================
echo   ForgeX Bot - Clean Setup
echo =====================================
echo.

REM Remove old venv
if exist "venv" (
    echo Removing old virtual environment...
    rmdir /s /q venv
)

REM Create fresh venv
echo Creating fresh virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip --quiet

REM Install compatible numpy first
echo Installing compatible NumPy...
pip install "numpy<2.0.0" --quiet

REM Install all dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet

echo.
echo =====================================
echo   Setup completed successfully!
echo   Run: run_bot.bat
echo =====================================

deactivate
pause
