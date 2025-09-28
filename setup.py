#!/usr/bin/env python3
"""
Setup script for CapCut Scraper
"""

import subprocess
import sys
import os

def install_requirements():
    """Install Python requirements"""
    print("📦 Installing Python packages...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])

def setup_directories():
    """Create necessary directories"""
    directories = [
        'downloads/videos',
        'downloads/thumbnails', 
        'output'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Created directory: {directory}")

def main():
    """Main setup function"""
    print("🚀 Setting up CapCut Scraper")
    print("=" * 30)
    
    try:
        setup_directories()
        install_requirements()
        
        print("\n✅ Setup complete!")
        print("💡 Run with: python capcut_scraper.py")
        print("📋 Make sure Chrome/Chromium is installed")
        print("🔗 ChromeDriver: https://chromedriver.chromium.org/")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")

if __name__ == "__main__":
    main()
