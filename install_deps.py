#!/usr/bin/env python3
"""
Dependency installer for Replit environment
Ensures all required packages are available
"""
import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def main():
    """Install all required dependencies"""
    packages = [
        'streamlit>=1.46.0',
        'numpy>=2.3.0',
        'opencv-python>=4.11.0.86',
        'pandas>=2.3.0',
        'plotly>=6.1.2',
        'scipy>=1.15.3',
        'pillow>=11.2.1',
        'sqlalchemy>=2.0.41',
        'psycopg2-binary>=2.9.10',
        'matplotlib>=3.7.0'
    ]
    
    print("🔧 Installing dependencies for Replit environment...")
    
    failed = []
    for package in packages:
        if not install_package(package):
            failed.append(package)
    
    if failed:
        print(f"\n❌ Failed to install: {', '.join(failed)}")
        return 1
    else:
        print("\n✅ All dependencies installed successfully!")
        return 0

if __name__ == "__main__":
    sys.exit(main())