#!/usr/bin/env python3

"""
Build script for creating a standalone executable of the Cloudbeds Sources Report application.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("🏨 Building Cloudbeds Sources Report Executable")
    print("=" * 50)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"✅ PyInstaller found: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        if not run_command("pip install pyinstaller", "Installing PyInstaller"):
            sys.exit(1)
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Clean previous builds
    build_dirs = ['build', 'dist', '__pycache__']
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            print(f"🧹 Cleaning {dir_name}...")
            shutil.rmtree(dir_name)
    
    # Create the executable
    pyinstaller_command = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=CloudbedsSourcesReport",
        "--add-data=templates;templates",
        "--add-data=static;static" if os.path.exists('static') else "",
        "--icon=icon.ico" if os.path.exists('icon.ico') else "",
        "--distpath=dist",
        "--workpath=build",
        "main.py"
    ]
    
    # Remove empty strings from command
    pyinstaller_command = [cmd for cmd in pyinstaller_command if cmd]
    
    command_str = " ".join(pyinstaller_command)
    
    if run_command(command_str, "Building executable"):
        print("\n🎉 Build completed successfully!")
        
        # Check if the executable was created
        exe_path = Path("dist/CloudbedsSourcesReport.exe")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📦 Executable created: {exe_path}")
            print(f"📏 File size: {size_mb:.1f} MB")
            print(f"📁 Full path: {exe_path.absolute()}")
        else:
            print("⚠️ Executable not found in expected location")
            
        print("\n📋 Next steps:")
        print("1. Test the executable by running it")
        print("2. Distribute the .exe file to users")
        print("3. Users only need the .exe file - no Python installation required")
        
    else:
        print("❌ Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()