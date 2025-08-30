#!/usr/bin/env python3
"""
Install dependencies for the Web Dashboard
Handles Python 3.13 compatibility issues
"""

import subprocess
import sys
import os

def install_packages():
    """Install packages with proper versions for Python 3.13"""
    
    print("🔧 Installing Web Dashboard dependencies...")
    print(f"Python version: {sys.version}")
    
    # Core packages that work with Python 3.13
    packages = [
        "fastapi",
        "uvicorn[standard]",
        "websockets",
        "python-multipart",
        "pyyaml",
        "psutil",
        "httpx",
        "python-dotenv",
        "aiofiles",
    ]
    
    # Install packages one by one for better error handling
    for package in packages:
        print(f"📦 Installing {package}...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Warning: Could not install {package}")
            print(f"   Error: {e.stderr}")
            # Continue with other packages
    
    # Try to install pydantic without specific version
    print("📦 Installing pydantic (latest compatible version)...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pydantic"],
            check=True
        )
        print("✅ pydantic installed successfully")
    except:
        print("⚠️ Warning: pydantic installation failed, using fallback")
        # Try older version that doesn't require compilation
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "pydantic==1.10.13"],
                check=True
            )
            print("✅ pydantic 1.10.13 installed as fallback")
        except:
            print("⚠️ pydantic installation failed - dashboard may have limited functionality")
    
    print("\n✅ Installation complete!")
    
    # Check what's installed
    print("\n📋 Installed packages:")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list"],
        capture_output=True,
        text=True
    )
    
    important_packages = ["fastapi", "uvicorn", "websockets", "pydantic"]
    for line in result.stdout.split('\n'):
        for pkg in important_packages:
            if pkg.lower() in line.lower():
                print(f"   {line.strip()}")

if __name__ == "__main__":
    install_packages()