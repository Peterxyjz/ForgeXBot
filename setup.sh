#!/bin/bash
echo "================================"
echo "   ForgeX Bot Setup Script"
echo "================================"

echo "Step 1: Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    exit 1
fi

echo "Step 2: Activating virtual environment..."
source venv/bin/activate

echo "Step 3: Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo "Step 4: Creating .env file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ".env file created from template"
else
    echo ".env file already exists"
fi

echo ""
echo "================================"
echo "   Setup completed successfully!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Run: python main.py --test"
echo "3. Run: python main.py"
echo ""
