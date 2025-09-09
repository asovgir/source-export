# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Cloudbeds Sources Report desktop application - a Flask-based web app that provides a GUI for viewing and exporting Cloudbeds property sources data via their API. The application can be packaged into a standalone executable for Windows distribution.

## Common Development Commands

### Running the Application
```bash
python main.py
```
This starts the Flask development server and automatically opens the application in the default web browser.

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Building Executable (Windows)
```bash
python build_exe.py
```
This creates a standalone .exe file using PyInstaller. The executable will be created in the `dist/` folder.

## Architecture

### Core Structure
- **main.py**: Primary Flask application with API integration logic
- **templates/index.html**: Single-page web interface  
- **build_exe.py**: PyInstaller build script for creating Windows executable
- **requirements.txt**: Python dependencies (Flask, requests, Werkzeug)

### Key Components

**Flask Application (`main.py`)**:
- Single-file Flask app with embedded web server
- Handles Cloudbeds API authentication and data fetching
- Provides paginated API calls with automatic retry logic
- Stores user configuration in `~/.cloudbeds_sources_config.json`
- Auto-opens web browser on startup when run as executable

**API Integration**:
- Uses Cloudbeds API v1.3 endpoints (`/getSources`, `/getRooms`)
- Implements pagination for large datasets
- Handles nested API response structures
- Processes and flattens complex source data for CSV export

**Build System**:
- PyInstaller configuration for Windows executable creation
- Bundles templates and static files into single executable
- Includes cleanup and verification steps

### Data Flow
1. User configures API credentials in web interface
2. Application validates connection to Cloudbeds API
3. Data is fetched with pagination and processed into flat structure
4. Results displayed in HTML table format
5. CSV export functionality available

## Configuration

The application automatically saves user settings to `~/.cloudbeds_sources_config.json` including:
- Cloudbeds API access token
- Property ID
- Other user preferences

## Dependencies

- **Flask 2.3.3**: Web framework
- **requests 2.31.0**: HTTP client for API calls  
- **Werkzeug 2.3.7**: WSGI utilities
- **PyInstaller**: For building executables (installed via build script)

## Development Notes

- This is a desktop application disguised as a web app - it runs a local Flask server and opens the browser
- The app is designed for single-user, local execution rather than web deployment
- Build process specifically targets Windows with .exe output
- No test framework is currently implemented
- Configuration is persisted locally, not in the repository