#!/usr/bin/env python3
"""
Quick run script for CapCut scraper
"""

import os
import subprocess
import sys

def main():
    print("🤖 CapCut Template Scraper")
    print("=" * 30)
    
    # Check if setup was run
    if not os.path.exists('output'):
        print("⚠️ Running setup first...")
        subprocess.run([sys.executable, 'setup.py'])
    
    # Run the scraper
    print("\n🚀 Starting scraper...")
    subprocess.run([sys.executable, 'capcut_scraper.py'])

if __name__ == "__main__":
    main()
