#!/usr/bin/env python
"""
Setup script for ForgeX Bot
Helps with initial configuration and dependency installation
"""

import os
import sys
import subprocess
import yaml
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.8+"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True


def install_requirements():
    """Install required packages"""
    print("\n📦 Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")
        print("   Try running: pip install -r requirements.txt")
        return False


def setup_config():
    """Interactive configuration setup"""
    print("\n⚙️  Configuration Setup")
    print("-" * 40)
    
    config_path = Path("config/config.yaml")
    
    if not config_path.exists():
        print("❌ config/config.yaml not found")
        return False
    
    # Load existing config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print("\nPlease enter your credentials (press Enter to skip):")
    
    # MT5 Configuration
    print("\n📊 MT5 Configuration:")
    mt5_login = input(f"  MT5 Login [{config['mt5']['login']}]: ").strip()
    if mt5_login:
        config['mt5']['login'] = int(mt5_login)
    
    mt5_password = input(f"  MT5 Password [***]: ").strip()
    if mt5_password:
        config['mt5']['password'] = mt5_password
    
    mt5_server = input(f"  MT5 Server [{config['mt5']['server']}]: ").strip()
    if mt5_server:
        config['mt5']['server'] = mt5_server
    
    # Telegram Configuration
    print("\n💬 Telegram Configuration:")
    bot_token = input(f"  Bot Token [{config['telegram']['bot_token'][:20]}...]: ").strip()
    if bot_token:
        config['telegram']['bot_token'] = bot_token
    
    chat_id = input(f"  Chat ID [{config['telegram']['chat_id']}]: ").strip()
    if chat_id:
        config['telegram']['chat_id'] = chat_id
    
    # Save configuration
    save = input("\n💾 Save configuration? (y/n): ").strip().lower()
    if save == 'y':
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        print("✅ Configuration saved")
        return True
    else:
        print("ℹ️  Configuration not saved")
        return False


def create_directories():
    """Create necessary directories"""
    directories = ['logs', 'config']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ Directories created")


def test_imports():
    """Test if all modules can be imported"""
    print("\n🔍 Testing imports...")
    modules = [
        'MetaTrader5',
        'pandas',
        'numpy',
        'yaml',
        'telegram'
    ]
    
    all_ok = True
    for module in modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            print(f"  ❌ {module} - not installed")
            all_ok = False
    
    return all_ok


def main():
    """Main setup function"""
    print("=" * 50)
    print("    ForgeX Bot - Setup Script")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Install requirements
    install_deps = input("\n📦 Install/update dependencies? (y/n): ").strip().lower()
    if install_deps == 'y':
        if not install_requirements():
            print("\n⚠️  Please install requirements manually")
    
    # Test imports
    if not test_imports():
        print("\n⚠️  Some modules are missing. Please run: pip install -r requirements.txt")
    
    # Setup configuration
    setup_conf = input("\n⚙️  Setup configuration? (y/n): ").strip().lower()
    if setup_conf == 'y':
        setup_config()
    
    print("\n" + "=" * 50)
    print("✅ Setup complete!")
    print("\nNext steps:")
    print("1. Edit config/config.yaml if needed")
    print("2. Test the bot: python main.py --test")
    print("3. Run the bot: python main.py")
    print("\nFor more information, see README.md")
    print("=" * 50)


if __name__ == "__main__":
    main()
