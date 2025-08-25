#!/bin/bash
echo "====================================="
echo "   ForgeX Bot v0.0.2"
echo "====================================="

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Please run setup.sh first or copy .env.example to .env"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please run setup.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Start bot
echo ""
echo "Starting ForgeX Bot..."
echo "Press Ctrl+C to stop"
echo ""
python main.py "$@"

# Cleanup
deactivate
