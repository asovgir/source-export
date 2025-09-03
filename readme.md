# Cloudbeds Sources Report

A desktop application for viewing and exporting Cloudbeds property sources data.

## Features

- 🏨 View all sources for a Cloudbeds property
- 📊 Display sources in a clean HTML table format
- 📄 Export data to CSV format
- ⚙️ Simple API configuration
- 🖥️ Standalone desktop application (no Python installation required)

## Setup for Development

1. **Install Python 3.7+**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

## Usage

1. **Launch the application**
   - Double-click the .exe file (if using executable)
   - Or run `python main.py` (if running from source)

2. **Configure API Settings**
   - Enter your Cloudbeds API Key
   - Enter your Property ID
   - Click "Test Connection" to verify
   - Click "Save Settings" to store credentials

3. **Load Sources Data**
   - Click "Load Sources" to fetch data from the API
   - View the data in the table

4. **Export Data**
   - Click "Export CSV" to download the data as a CSV file

## API Requirements

You need:
- **Cloudbeds API Key**: Get this from your Cloudbeds account
- **Property ID**: Your specific property identifier

The application uses the Cloudbeds API endpoint:
- `GET /api/v1.3/getSources`

## Project Structure

```
cloudbeds-sources-report/
├── main.py                 # Main Flask application
├── requirements.txt        # Python dependencies
├── build_exe.py           # Build script for executable
├── README.md              # This file
└── templates/
    └── index.html         # Single-page application template
```

## Configuration

Settings are automatically saved to:
- `~/.cloudbeds_sources_config.json`

## Troubleshooting

### API Connection Issues
- Verify your API key is correct
- Check that your Property ID is valid
- Ensure you have internet connectivity

### Build Issues
- Make sure PyInstaller is installed
- Check that all template files exist
- Verify Python version compatibility

## Building Executable (Windows)

To create a standalone .exe file:

1. **Install PyInstaller:**
   ```bash
   pip install pyinstaller
   ```

2. **Run the build script:**
   ```bash
   python build_exe.py
   ```

3. **Find the executable in the `dist` folder:**
   ```
   dist/CloudbedsSourcesReport.exe
   ```  

# Building for macOS

Complete step-by-step instructions for building the Cloudbeds Reports application on macOS.

## Prerequisites

1. **Check Python 3 Installation**
   ```bash
   python3 --version
   ```
   Requires Python 3.8 or newer.

## Installing Dependencies

1. **Install Homebrew (if not already installed)**
   ```bash
   # Check if Homebrew is installed:
   which brew

   # If not installed, install it:
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Python 3 (if needed)**
   ```bash
   brew install python3

   # Verify installation:
   python3 --version
   pip3 --version
   ```

3. **Install Git (if not already installed)**
   ```bash
   # Check if Git is installed:
   git --version

   # If not installed:
   brew install git
   ```

## Building the Application

1. **Clone the Repository**
   ```bash
   # Create workspace on Desktop:
   cd ~/Desktop

   # Clone the repository:
   git clone https://github.com/asovgir/source-export.git

   # Navigate to project:
   cd source-export
   ```

2. **Set Up Python Environment**
   ```bash
   # Create virtual environment:
   python3 -m venv venv

   # Activate virtual environment:
   source venv/bin/activate
   ```

3. **Install Required Python Packages**
   ```bash
   # Install required packages:
   pip install --upgrade pip
   pip install flask requests pyinstaller
   ```

4. **Verify Project Structure**
   ```bash
   # Check that all required files are present:
   ls -la

   # Should see:
   # - build_exe.py
   # - templates/ folder with index.html
   # - README.md
   ```

5. **Create Build Script**
   ```bash
   # Create the build script:
   nano build_app.py
   ```
   Copy and paste this build script:
   ```python
   #!/usr/bin/env python3
   import os
   import sys
   import subprocess
   import shutil
   from pathlib import Path

   def find_main_file():
       """Find the main Python file"""
       possible_names = ['build_exe.py', 'main.py', 'app.py']
       
       for name in possible_names:
           if os.path.exists(name):
               print(f"Found main file: {name}")
               return name
       
       print("ERROR: Could not find main Python file!")
       return None

   def build_mac_app():
       """Build the macOS application"""
       print("Building Cloudbeds Reports for macOS...")
       
       main_file = find_main_file()
       if not main_file:
           return False
       
       if not os.path.exists('templates/index.html'):
           print("ERROR: templates/index.html not found!")
           return False
       
       cmd = [
           'pyinstaller',
           '--onefile',
           '--windowed',
           '--name=CloudbedsReports',
           '--add-data=templates:templates',
           '--distpath=dist',
           '--workpath=build',
           '--specpath=.',
           '--clean',
           main_file
       ]
       
       try:
           result = subprocess.run(cmd, check=True, capture_output=True, text=True)
           print("Build successful!")
           
           exe_path = os.path.join('dist', 'CloudbedsReports')
           if os.path.exists(exe_path):
               os.chmod(exe_path, 0o755)
               return True
           return False
               
       except subprocess.CalledProcessError as e:
           print(f"Build failed: {e}")
           return False

   def create_distribution():
       """Create distribution package"""
       dist_folder = "Cloudbeds Reports"
       if os.path.exists(dist_folder):
           shutil.rmtree(dist_folder)
       
       os.makedirs(dist_folder)
       shutil.copy2('dist/CloudbedsReports', f'{dist_folder}/')
       
       readme_content = """Cloudbeds Reports - macOS Application

   Installation:
   1. Copy CloudbedsReports to your Applications folder (optional)
   2. Double-click CloudbedsReports to run
   3. If macOS blocks it, right-click and select "Open"

   Usage:
   1. App automatically opens web browser
   2. Configure your Cloudbeds API key
   3. Load and export data as CSV files
   """
       
       with open(f'{dist_folder}/README.txt', 'w') as f:
           f.write(readme_content)
       
       shutil.make_archive('CloudbedsReports-macOS', 'zip', '.', dist_folder)
       return True

   if __name__ == "__main__":
       print("Cloudbeds Reports - macOS Build Script")
       if build_mac_app() and create_distribution():
           print("BUILD COMPLETE! CloudbedsReports-macOS.zip is ready!")
       else:
           print("Build failed!")
           sys.exit(1)
   ```
   Save and exit (Ctrl + X, Y, Enter).

6. **Run the Build**
   ```bash
   python3 build_app.py
   ```

7. **Test the Application**
   - Open Finder and navigate to `source-export/dist/`
   - Double-click `CloudbedsReports`
   - Application should start and open browser automatically

## Troubleshooting

- **If git clone fails:** Try `git clone https://github.com/asovgir/source-export.git`
- **If PyInstaller fails:** Run `pip install --upgrade pyinstaller`
- **If executable won't run:** Run `chmod +x dist/CloudbedsReports`

## Final Output

The build creates **CloudbedsReports-macOS.zip** - this is the file to distribute.

**Build Time:** Approximately 15-25 minutes
## License

This project is for internal use with Cloudbeds API integration.
