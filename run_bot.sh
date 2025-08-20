#!/bin/bash

echo "====================================="
echo "  MT5 Price Action Bot - Linux/Mac"
echo "====================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed"
    echo "Please install Python 3.8+ first"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python $required_version+ is required (found $python_version)"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created."
    echo
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
if ! pip show MetaTrader5 &> /dev/null; then
    echo "Installing requirements..."
    pip install -r requirements.txt
    echo
fi

# Run the bot
echo "Starting MT5 Price Action Bot..."
echo "Press Ctrl+C to stop the bot"
echo
python main.py "$@"

# Deactivate virtual environment
deactivate

echo
echo "Bot stopped."
