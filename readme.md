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

## Building Executable

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

## License

This project is for internal use with Cloudbeds API integration.