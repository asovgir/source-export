#!/usr/bin/env python3

import os
import json
import requests
import webbrowser
import threading
import time
import sys
import csv
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response

# Handle PyInstaller bundle paths
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    application_path = sys._MEIPASS
else:
    # Running as script
    application_path = os.path.dirname(os.path.abspath(__file__))

# Set up paths for templates and static files
template_dir = os.path.join(application_path, 'templates')
static_dir = os.path.join(application_path, 'static')

# Flask app configuration with correct paths
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config['SECRET_KEY'] = 'cloudbeds-sources-desktop-app-secret'

# Configuration file handling (using JSON instead of YAML)
CONFIG_FILE = Path.home() / '.cloudbeds_sources_config.json'

def load_config():
    """Load configuration from JSON file"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f) or {}
    except Exception as e:
        print(f"Warning: Could not load configuration: {e}")
    return {}

def save_config(config):
    """Save configuration to JSON file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Configuration saved to: {CONFIG_FILE}")
    except Exception as e:
        print(f"Warning: Could not save configuration: {e}")

def get_credentials():
    """Get API credentials from config"""
    config = load_config()
    return {
        'access_token': config.get('access_token'),
        'property_id': config.get('property_id', '6000')
    }

# API URLs
SOURCES_URL = "https://api.cloudbeds.com/api/v1.3/getSources"
TAXES_FEES_URL = "https://api.cloudbeds.com/api/v1.3/getTaxesAndFees"

def make_api_call(url, params, credentials):
    """Make API call to Cloudbeds using Bearer token authentication"""
    headers = {
        "Authorization": f"Bearer {credentials['access_token']}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        print(f"🔗 API call to {url} - Status: {response.status_code}")
        print(f"📄 Response headers: {dict(response.headers)}")
        
        # Log first 500 characters of response for debugging
        response_preview = response.text[:500] if response.text else "Empty response"
        print(f"📋 Response preview: {response_preview}")
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                return {'success': True, 'data': json_data}
            except ValueError as e:
                print(f"❌ JSON parsing error: {e}")
                return {'success': False, 'error': f"Invalid JSON response: {response.text[:200]}..."}
        elif response.status_code == 401:
            return {'success': False, 'error': "Authentication failed. Please check your access token."}
        elif response.status_code == 403:
            return {'success': False, 'error': "Access forbidden. Please check your access token permissions."}
        elif response.status_code == 429:
            return {'success': False, 'error': "Rate limit exceeded. Please try again in a few minutes."}
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('message', response.text)
            except:
                error_msg = response.text[:200] if response.text else "Unknown error"
            return {'success': False, 'error': f"API Error: {response.status_code} - {error_msg}"}
    except requests.exceptions.Timeout:
        return {'success': False, 'error': "Request timed out. Please check your internet connection."}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': "Connection error. Please check your internet connection."}
    except Exception as e:
        return {'success': False, 'error': f"Connection error: {str(e)}"}

def flatten_source_data(source):
    """Flatten source data for table display"""
    flattened = {}
    
    # Basic source info
    flattened['propertyID'] = source.get('propertyID', '')
    flattened['sourceID'] = source.get('sourceID', '')
    flattened['sourceName'] = source.get('sourceName', '')
    flattened['isThirdParty'] = source.get('isThirdParty', '')
    flattened['status'] = source.get('status', '')
    flattened['commission'] = source.get('commission', '')
    flattened['paymentCollect'] = source.get('paymentCollect', '')
    
    # Handle taxes
    taxes = source.get('taxes', [])
    if taxes:
        for i, tax in enumerate(taxes):
            flattened[f'tax_{i+1}_taxID'] = tax.get('taxID', '')
            flattened[f'tax_{i+1}_name'] = tax.get('name', '')
            flattened[f'tax_{i+1}_amount'] = tax.get('amount', '')
            flattened[f'tax_{i+1}_amountType'] = tax.get('amountType', '')
            flattened[f'tax_{i+1}_type'] = tax.get('type', '')
    else:
        flattened['taxes'] = 'None'
    
    # Handle fees
    fees = source.get('fees', [])
    if fees:
        for i, fee in enumerate(fees):
            flattened[f'fee_{i+1}_feeID'] = fee.get('feeID', '')
            flattened[f'fee_{i+1}_name'] = fee.get('name', '')
            flattened[f'fee_{i+1}_amount'] = fee.get('amount', '')
            flattened[f'fee_{i+1}_amountType'] = fee.get('amountType', '')
            flattened[f'fee_{i+1}_type'] = fee.get('type', '')
    else:
        flattened['fees'] = 'None'
    
    return flattened

def get_all_possible_columns(sources_data):
    """Get all possible column names from all sources"""
    all_columns = set()
    for source in sources_data:
        flattened = flatten_source_data(source)
        all_columns.update(flattened.keys())
    
    # Sort columns for consistent ordering
    basic_columns = ['propertyID', 'sourceID', 'sourceName', 'isThirdParty', 'status', 'commission', 'paymentCollect']
    sorted_columns = []
    
    # Add basic columns first
    for col in basic_columns:
        if col in all_columns:
            sorted_columns.append(col)
            all_columns.remove(col)
    
    # Add remaining columns sorted
    sorted_columns.extend(sorted(all_columns))
    
    return sorted_columns

def flatten_taxes_fees_data(item):
    """Flatten taxes and fees data for table display"""
    flattened = {}
    
    # Handle all possible fields from the taxes and fees response
    for key, value in item.items():
        if isinstance(value, dict):
            # Flatten nested objects
            for nested_key, nested_value in value.items():
                flattened[f"{key}_{nested_key}"] = nested_value
        elif isinstance(value, list):
            # Handle arrays by joining them or creating indexed fields
            if value:
                if len(value) == 1 and isinstance(value[0], (str, int, float, bool)):
                    flattened[key] = value[0]
                else:
                    for i, list_item in enumerate(value):
                        if isinstance(list_item, dict):
                            for nested_key, nested_value in list_item.items():
                                flattened[f"{key}_{i+1}_{nested_key}"] = nested_value
                        else:
                            flattened[f"{key}_{i+1}"] = list_item
            else:
                flattened[key] = 'None'
        else:
            flattened[key] = value
    
    return flattened

def get_all_possible_taxes_fees_columns(data):
    """Get all possible column names from all taxes/fees items"""
    all_columns = set()
    for item in data:
        flattened = flatten_taxes_fees_data(item)
        all_columns.update(flattened.keys())
    
    # Sort columns for consistent ordering
    basic_columns = ['propertyID', 'taxID', 'feeID', 'name', 'amount', 'amountType', 'type', 'status']
    sorted_columns = []
    
    # Add basic columns first if they exist
    for col in basic_columns:
        if col in all_columns:
            sorted_columns.append(col)
            all_columns.remove(col)
    
    # Add remaining columns sorted
    sorted_columns.extend(sorted(all_columns))
    
    return sorted_columns

# Routes
@app.route('/')
def index():
    """Main page - single page app"""
    config = load_config()
    return render_template('index.html', config=config)

@app.route('/api/save-settings', methods=['POST'])
def save_settings():
    """Save API credentials via AJAX"""
    try:
        data = request.get_json()
        config = {
            'access_token': data.get('access_token', '').strip(),
            'property_id': data.get('property_id', '6000').strip()
        }
        
        save_config(config)
        return jsonify({'success': True, 'message': 'Settings saved successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to save settings: {str(e)}'})

@app.route('/api/get-settings')
def get_settings():
    """Get current settings"""
    config = load_config()
    return jsonify({'success': True, 'data': config})

@app.route('/api/test-connection')
def test_connection():
    """Test API connection"""
    print("🧪 Testing API connection...")
    
    # Get current form data if available, otherwise use saved config
    form_access_token = request.args.get('access_token')
    form_property_id = request.args.get('property_id')
    
    if form_access_token and form_property_id:
        # Use form data for testing (before saving)
        credentials = {
            'access_token': form_access_token.strip(),
            'property_id': form_property_id.strip()
        }
        print("🔧 Using form data for test")
    else:
        # Use saved credentials
        credentials = get_credentials()
        print("🔧 Using saved credentials for test")
    
    # Validate credentials
    if not credentials['access_token'] or not credentials['access_token'].strip():
        return jsonify({
            'success': False, 
            'error': 'Please configure your access token first.'
        })
    
    if not credentials['property_id'] or not credentials['property_id'].strip():
        return jsonify({
            'success': False, 
            'error': 'Please provide a valid Property ID.'
        })
    
    print(f"🔗 Testing API call for property: {credentials['property_id']}")
    
    result = make_api_call(SOURCES_URL, {
        'propertyID': credentials['property_id']
    }, credentials)
    
    if result['success']:
        try:
            response_data = result['data']
            if isinstance(response_data, dict) and 'data' in response_data:
                sources_data = response_data.get('data', [])
                if isinstance(sources_data, list) and len(sources_data) > 0:
                    sources_count = len(sources_data[0]) if sources_data[0] else 0
                else:
                    sources_count = 0
                    
                print(f"✅ API test successful - found {sources_count} sources")
                
                if sources_count > 0:
                    message = f'Connection successful! Found {sources_count} sources in your property.'
                else:
                    message = 'Connection successful! No sources found, but API access is working.'
                
                return jsonify({
                    'success': True, 
                    'message': message,
                    'details': {
                        'property_id': credentials['property_id'],
                        'sources_found': sources_count
                    }
                })
            else:
                return jsonify({
                    'success': False, 
                    'error': 'API connection successful but received unexpected response format.'
                })
        except Exception as e:
            print(f"⚠️ API response validation error: {e}")
            return jsonify({
                'success': False, 
                'error': f'API connection successful but response validation failed: {str(e)}'
            })
    else:
        print(f"❌ API test failed: {result['error']}")
        return jsonify({
            'success': False, 
            'error': result['error']
        })

@app.route('/api/sources')
def get_sources():
    """Main API endpoint for fetching sources"""
    try:
        credentials = get_credentials()
        
        if not credentials['access_token']:
            return jsonify({'success': False, 'error': 'Access token not configured. Please check settings.'})
        
        print(f"🚀 Fetching sources for property {credentials['property_id']}")
        print(f"🔑 Using access token: {credentials['access_token'][:10]}...")
        
        # Fetch sources
        sources_response = make_api_call(SOURCES_URL, {
            'propertyID': credentials['property_id']
        }, credentials)
        
        if not sources_response['success']:
            print(f"❌ Sources API call failed: {sources_response['error']}")
            return jsonify({'success': False, 'error': f"Failed to fetch sources: {sources_response['error']}"})
        
        # Extract sources data
        response_data = sources_response['data']
        print(f"📊 Raw API response structure: {type(response_data)}")
        print(f"📊 Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
        
        sources_data = []
        
        # Handle the nested structure from your JSON example
        if 'data' in response_data and isinstance(response_data['data'], list):
            if len(response_data['data']) > 0 and isinstance(response_data['data'][0], list):
                sources_data = response_data['data'][0]
                print(f"📊 Found nested list structure with {len(sources_data)} items")
            else:
                sources_data = response_data['data']
                print(f"📊 Found direct list structure with {len(sources_data)} items")
        elif isinstance(response_data, list):
            sources_data = response_data
            print(f"📊 Response is direct list with {len(sources_data)} items")
        else:
            print(f"⚠️ Unexpected response structure: {response_data}")
            return jsonify({'success': False, 'error': f"Unexpected API response structure: {type(response_data)}"})
        
        print(f"Found {len(sources_data)} sources")
        
        if not sources_data:
            return jsonify({
                'success': True, 
                'data': {
                    'sources': [],
                    'columns': [],
                    'count': 0
                }
            })
        
        # Get all possible columns for consistent table structure
        all_columns = get_all_possible_columns(sources_data)
        print(f"📊 Generated {len(all_columns)} columns")
        
        # Flatten all sources data
        flattened_sources = []
        for i, source in enumerate(sources_data):
            try:
                flattened = flatten_source_data(source)
                # Ensure all columns are present (fill missing with empty string)
                for col in all_columns:
                    if col not in flattened:
                        flattened[col] = ''
                flattened_sources.append(flattened)
                print(f"📊 Processed source {i+1}/{len(sources_data)}")
            except Exception as e:
                print(f"❌ Error processing source {i}: {e}")
                continue
        
        print(f"✅ Successfully processed {len(flattened_sources)} sources")
        
        return jsonify({
            'success': True, 
            'data': {
                'sources': flattened_sources,
                'columns': all_columns,
                'count': len(flattened_sources)
            }
        })
    
    except Exception as e:
        print(f"❌ Critical error in get_sources: {e}")
        return jsonify({'success': False, 'error': f"Critical error: {str(e)}"})

@app.route('/api/taxes-fees')
def get_taxes_fees():
    """API endpoint for fetching taxes and fees"""
    credentials = get_credentials()
    
    if not credentials['access_token']:
        return jsonify({'success': False, 'error': 'Access token not configured. Please check settings.'})
    
    print(f"🚀 Fetching taxes and fees for property {credentials['property_id']}")
    
    # Fetch taxes and fees
    response = make_api_call(TAXES_FEES_URL, {
        'propertyID': credentials['property_id']
    }, credentials)
    
    if not response['success']:
        return jsonify({'success': False, 'error': f"Failed to fetch taxes and fees: {response['error']}"})
    
    # Extract data
    response_data = response['data']
    taxes_fees_data = []
    
    # Handle the response structure
    if 'data' in response_data:
        if isinstance(response_data['data'], list):
            taxes_fees_data = response_data['data']
        elif isinstance(response_data['data'], dict):
            # If data is an object, convert to list
            taxes_fees_data = [response_data['data']]
    else:
        # If no 'data' key, assume the response itself is the data
        if isinstance(response_data, list):
            taxes_fees_data = response_data
        else:
            taxes_fees_data = [response_data]
    
    print(f"Found {len(taxes_fees_data)} taxes and fees items")
    
    # Get all possible columns for consistent table structure
    all_columns = get_all_possible_taxes_fees_columns(taxes_fees_data)
    
    # Flatten all data
    flattened_data = []
    for item in taxes_fees_data:
        flattened = flatten_taxes_fees_data(item)
        # Ensure all columns are present (fill missing with empty string)
        for col in all_columns:
            if col not in flattened:
                flattened[col] = ''
        flattened_data.append(flattened)
    
    return jsonify({
        'success': True, 
        'data': {
            'items': flattened_data,
            'columns': all_columns,
            'count': len(flattened_data)
        }
    })

@app.route('/export/csv')
def export_csv():
    """Export sources data to CSV"""
    data_type = request.args.get('type', 'sources')
    credentials = get_credentials()
    
    if not credentials['access_token']:
        return "Access token not configured", 400
    
    print(f"📊 Exporting {data_type} to CSV for property {credentials['property_id']}")
    
    if data_type == 'taxes-fees':
        # Fetch taxes and fees data
        response = make_api_call(TAXES_FEES_URL, {
            'propertyID': credentials['property_id']
        }, credentials)
        
        if not response['success']:
            return f"Failed to fetch taxes and fees: {response['error']}", 500
        
        # Extract and process data
        response_data = response['data']
        data_items = []
        
        if 'data' in response_data:
            if isinstance(response_data['data'], list):
                data_items = response_data['data']
            elif isinstance(response_data['data'], dict):
                data_items = [response_data['data']]
        else:
            if isinstance(response_data, list):
                data_items = response_data
            else:
                data_items = [response_data]
        
        # Get all columns and flatten data
        all_columns = get_all_possible_taxes_fees_columns(data_items)
        flattened_data = []
        for item in data_items:
            flattened = flatten_taxes_fees_data(item)
            # Ensure all columns are present
            for col in all_columns:
                if col not in flattened:
                    flattened[col] = ''
            flattened_data.append(flattened)
        
        filename_prefix = "cloudbeds_taxes_fees"
        
    else:
        # Fetch sources data (existing functionality)
        response = make_api_call(SOURCES_URL, {
            'propertyID': credentials['property_id']
        }, credentials)
        
        if not response['success']:
            return f"Failed to fetch sources: {response['error']}", 500
        
        # Extract and process sources data
        response_data = response['data']
        data_items = []
        
        if 'data' in response_data and isinstance(response_data['data'], list):
            if len(response_data['data']) > 0 and isinstance(response_data['data'][0], list):
                data_items = response_data['data'][0]
            else:
                data_items = response_data['data']
        
        # Get all columns and flatten data
        all_columns = get_all_possible_columns(data_items)
        flattened_data = []
        for item in data_items:
            flattened = flatten_source_data(item)
            # Ensure all columns are present
            for col in all_columns:
                if col not in flattened:
                    flattened[col] = ''
            flattened_data.append(flattened)
        
        filename_prefix = "cloudbeds_sources"
    
    # Create CSV response
    output = []
    
    # Write header
    output.append(','.join(f'"{col}"' for col in all_columns))
    
    # Write data rows
    for item in flattened_data:
        row = []
        for col in all_columns:
            value = str(item.get(col, ''))
            # Escape quotes in CSV
            value = value.replace('"', '""')
            row.append(f'"{value}"')
        output.append(','.join(row))
    
    csv_content = '\n'.join(output)
    
    # Create response
    response = make_response(csv_content)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={filename_prefix}_{credentials["property_id"]}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    print(f"✅ CSV export completed - {len(flattened_data)} items exported")
    
    return response

@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Shutdown endpoint for desktop app"""
    print("🛑 Shutting down application...")
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        # For newer versions of Werkzeug
        os._exit(0)
    func()
    return 'Server shutting down...'

def open_browser():
    """Open browser after a short delay"""
    time.sleep(2)
    webbrowser.open('http://localhost:5000')

def find_free_port():
    """Find a free port starting from 5000"""
    import socket
    for port in range(5000, 5100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return 5000  # fallback

if __name__ == '__main__':
    print("\n🏨 Cloudbeds Sources Report - Desktop App")
    print("=" * 50)
    
    # Debug: Print paths when running as executable
    if getattr(sys, 'frozen', False):
        print(f"📁 Template directory: {template_dir}")
        print(f"📁 Static directory: {static_dir}")
        print(f"📁 Application path: {application_path}")
    
    # Find an available port
    port = find_free_port()
    
    print(f"📊 Starting server on http://localhost:{port}")
    print("🌐 Opening browser automatically...")
    print("❌ Close this window to stop the application\n")
    
    # Auto-open browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        # Start the Flask server
        app.run(host='127.0.0.1', port=port, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        input("Press Enter to close...")
        sys.exit(1)