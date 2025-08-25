@echo off
echo ================================
echo   ForgeX Bot Setup Script
echo ================================

echo Step 1: Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo Step 2: Activating virtual environment...
call venv\Scripts\activate.bat

echo Step 3: Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo Step 4: Creating .env file...
if not exist .env (
    copy .env.example .env
    echo .env file created from template
) else (
    echo .env file already exists
)

echo.
echo ================================
echo   Setup completed successfully!
echo ================================
echo.
echo Next steps:
echo 1. Edit .env file with your credentials
echo 2. Run: python main.py --test
echo 3. Run: python main.py
echo.
pause
