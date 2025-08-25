#!/usr/bin/env python3
"""
Simple setup script for ForgeX Bot
Creates virtual environment and installs dependencies
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Main setup function"""
    print("=" * 40)
    print("  ForgeX Bot - Simple Setup")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    
    # Create virtual environment
    print("\n📁 Creating virtual environment...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
        print("✅ Virtual environment created")
    except subprocess.CalledProcessError:
        print("❌ Failed to create virtual environment")
        sys.exit(1)
    
    # Install requirements
    print("\n📦 Installing requirements...")
    pip_path = "venv/Scripts/pip" if os.name == "nt" else "venv/bin/pip"
    
    try:
        subprocess.check_call([pip_path, "install", "-r", "requirements.txt"])
        print("✅ Requirements installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")
        sys.exit(1)
    
    # Create .env file
    print("\n⚙️  Creating .env file...")
    if not Path(".env").exists():
        subprocess.run(["cp", ".env.example", ".env"] if os.name != "nt" else ["copy", ".env.example", ".env"], shell=True)
        print("✅ .env file created from template")
    else:
        print("ℹ️  .env file already exists")
    
    print("\n" + "=" * 40)
    print("✅ Setup completed!")
    print("\nNext steps:")
    print("1. Edit .env with your credentials")
    print("2. Test: python main.py --test")
    print("3. Run: python main.py")
    print("=" * 40)


if __name__ == "__main__":
    main()
