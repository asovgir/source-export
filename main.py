#!/usr/bin/env python3

import os
import json
import requests
import webbrowser
import threading
import time
import sys
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, make_response

# Flask setup
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

template_dir = os.path.join(application_path, 'templates')
static_dir = os.path.join(application_path, 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config['SECRET_KEY'] = 'cloudbeds-reports-secret'

# Configuration
CONFIG_FILE = Path.home() / '.cloudbeds_sources_config.json'

def load_config():
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f) or {}
    except Exception as e:
        print(f"Warning: Could not load configuration: {e}")
    return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Configuration saved to: {CONFIG_FILE}")
    except Exception as e:
        print(f"Warning: Could not save configuration: {e}")

def get_credentials():
    config = load_config()
    return {
        'access_token': config.get('access_token'),
        'property_id': config.get('property_id', '6000')
    }

# API URLs
SOURCES_URL = "https://api.cloudbeds.com/api/v1.3/getSources"
TAXES_FEES_URL = "https://api.cloudbeds.com/api/v1.3/getTaxesAndFees"
ROOM_TYPES_URL = "https://api.cloudbeds.com/api/v1.3/getRoomTypes"
ROOMS_URL = "https://api.cloudbeds.com/api/v1.3/getRooms"
PAYMENT_METHODS_URL = "https://api.cloudbeds.com/api/v1.3/getPaymentMethods"
ITEMS_URL = "https://api.cloudbeds.com/api/v1.3/getItems"

def make_api_call(url, params, credentials):
    headers = {
        "Authorization": f"Bearer {credentials['access_token']}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"🚀 Making API call to: {url}")
        print(f"🚀 Parameters: {params}")
        print(f"🚀 Token present: {bool(credentials['access_token'])}")
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        print(f"🔗 API call to {url} - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📋 Response preview: {str(data)[:200]}...")
            return {'success': True, 'data': data}
        else:
            error_msg = f"HTTP {response.status_code}"
            try:
                error_data = response.json()
                error_msg = error_data.get('message', error_msg)
                print(f"❌ API Error response: {error_data}")
            except:
                print(f"❌ API Error - no JSON response: {response.text}")
                pass
            return {'success': False, 'error': error_msg}
    except requests.exceptions.Timeout:
        print("❌ API call timed out")
        return {'success': False, 'error': "Request timed out after 30 seconds"}
    except requests.exceptions.ConnectionError:
        print("❌ Connection error")
        return {'success': False, 'error': "Connection error - check your internet connection"}
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': f"Connection error: {str(e)}"}

# Data processing functions
def safe_get(obj, key, default=''):
    """Safely get a value from a dictionary"""
    if obj is None or not isinstance(obj, dict):
        return default
    return obj.get(key, default)

def process_sources_data(sources_response):
    """Process sources API response into flat table data"""
    if not sources_response or not sources_response.get('success'):
        return []
    
    data = sources_response['data']
    
    # Handle nested structure: {"data": [[ sources... ]] }
    sources = []
    if isinstance(data, dict) and 'data' in data:
        nested_data = data['data']
        if isinstance(nested_data, list) and len(nested_data) > 0:
            if isinstance(nested_data[0], list):
                sources = nested_data[0]  # Double nested
            else:
                sources = nested_data  # Single nested
    elif isinstance(data, list):
        sources = data
    
    print(f"📊 Processing {len(sources)} sources")
    
    processed = []
    for i, source in enumerate(sources):
        if source is None:
            print(f"⚠️ Skipping None source at index {i}")
            continue
        
        try:
            row = {}
            
            # Basic fields
            row['propertyID'] = safe_get(source, 'propertyID')
            row['sourceID'] = safe_get(source, 'sourceID')
            row['sourceName'] = safe_get(source, 'sourceName')
            row['isThirdParty'] = safe_get(source, 'isThirdParty')
            row['status'] = safe_get(source, 'status')
            row['commission'] = safe_get(source, 'commission')
            row['paymentCollect'] = safe_get(source, 'paymentCollect')
            
            # Process taxes
            taxes = source.get('taxes', [])
            if isinstance(taxes, list) and taxes:
                for idx, tax in enumerate(taxes):
                    if tax is not None and isinstance(tax, dict):
                        num = idx + 1
                        row[f'tax_{num}_taxID'] = safe_get(tax, 'taxID')
                        row[f'tax_{num}_name'] = safe_get(tax, 'name')
                        row[f'tax_{num}_amount'] = safe_get(tax, 'amount')
                        row[f'tax_{num}_amountType'] = safe_get(tax, 'amountType')
                        row[f'tax_{num}_type'] = safe_get(tax, 'type')
            
            # Process fees
            fees = source.get('fees', [])
            if isinstance(fees, list) and fees:
                for idx, fee in enumerate(fees):
                    if fee is not None and isinstance(fee, dict):
                        num = idx + 1
                        row[f'fee_{num}_feeID'] = safe_get(fee, 'feeID')
                        row[f'fee_{num}_name'] = safe_get(fee, 'name')
                        row[f'fee_{num}_amount'] = safe_get(fee, 'amount')
                        row[f'fee_{num}_amountType'] = safe_get(fee, 'amountType')
                        row[f'fee_{num}_type'] = safe_get(fee, 'type')
            
            processed.append(row)
            print(f"✅ Processed source {i+1}: {row.get('sourceName', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Error processing source {i}: {e}")
            continue
    
    return processed

def process_payment_methods_data(response):
    """Process payment methods API response"""
    if not response or not response.get('success'):
        print("❌ Payment methods response is not successful")
        return []
    
    # The response structure from make_api_call is: {'success': True, 'data': actual_api_response}
    # And the actual_api_response is: {'success': True, 'data': {'propertyID': '6000', 'methods': [...], 'gateway': {...}}}
    # So we need to get response['data']['data'] to access the actual payment data
    
    outer_data = response['data']
    print(f"📊 Outer data keys: {list(outer_data.keys()) if isinstance(outer_data, dict) else 'Not a dict'}")
    
    # Handle the nested response structure
    if isinstance(outer_data, dict) and 'data' in outer_data:
        data = outer_data['data']
        print(f"📊 Inner data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
    else:
        data = outer_data
        print(f"📊 Using outer data directly: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
    
    processed = []
    
    # Add gateway information first
    if isinstance(data, dict) and 'gateway' in data and isinstance(data['gateway'], dict):
        gateway_info = data['gateway']
        gateway_row = {
            'data_type': 'Gateway',
            'property_id': data.get('propertyID', ''),
            'gateway_name': gateway_info.get('name', ''),
            'gateway_currency': gateway_info.get('currency', ''),
            'method_type': '',
            'method_code': '',
            'method_name': '',
            'card_types': ''
        }
        processed.append(gateway_row)
        print(f"✅ Added gateway: {gateway_info.get('name')}")
    
    # Process payment methods
    if isinstance(data, dict) and 'methods' in data and isinstance(data['methods'], list):
        methods = data['methods']
        print(f"📊 Processing {len(methods)} payment methods from methods array")
        
        # Get gateway info for context
        gateway_info = data.get('gateway', {})
        
        for i, method in enumerate(methods):
            if method is None:
                print(f"⚠️ Skipping None method at index {i}")
                continue
            
            print(f"🔍 Processing method {i+1}: {safe_get(method, 'name', 'No name')}")
            
            method_row = {
                'data_type': 'Payment Method',
                'property_id': data.get('propertyID', ''),
                'gateway_name': gateway_info.get('name', '') if gateway_info else '',
                'gateway_currency': gateway_info.get('currency', '') if gateway_info else '',
                'method_type': safe_get(method, 'method'),
                'method_code': safe_get(method, 'code'),
                'method_name': safe_get(method, 'name'),
                'card_types': ''
            }
            
            # Handle card types if they exist
            card_types = method.get('cardTypes', [])
            if isinstance(card_types, list) and card_types:
                card_type_names = []
                for card_type in card_types:
                    if isinstance(card_type, dict):
                        card_name = card_type.get('cardName', '')
                        card_code = card_type.get('cardCode', '')
                        if card_name:
                            card_type_names.append(f"{card_name} ({card_code})")
                method_row['card_types'] = ', '.join(card_type_names)
            
            processed.append(method_row)
            print(f"✅ Added payment method {i+1}: {method_row['method_name']}")
    else:
        print("❌ No methods array found in data!")
        print(f"❌ Data keys available: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        print(f"❌ Data type: {type(data)}")
    
    print(f"📊 Total processed payment items: {len(processed)}")
    print(f"📊 Processed items: {[item.get('data_type', 'Unknown') + ': ' + item.get('method_name', item.get('gateway_name', 'No name')) for item in processed]}")
    
    return processed

def process_items_data(response):
    """Process items API response into flat table data"""
    if not response or not response.get('success'):
        print("❌ Items response is not successful")
        return []
    
    data = response['data']
    print(f"📊 Processing items data: {type(data)}")
    
    # Handle nested structure if needed
    if isinstance(data, dict) and 'data' in data:
        items = data['data']
        print(f"📊 Found nested data structure with {len(items)} items")
    elif isinstance(data, list):
        items = data
        print(f"📊 Found direct list with {len(items)} items")
    else:
        print("❌ Unexpected data structure")
        return []
    
    processed = []
    for i, item in enumerate(items):
        if item is None:
            print(f"⚠️ Skipping None item at index {i}")
            continue
        
        try:
            row = {}
            
            # Basic fields
            row['itemID'] = safe_get(item, 'itemID')
            row['itemType'] = safe_get(item, 'itemType')
            row['sku'] = safe_get(item, 'sku')
            row['itemCode'] = safe_get(item, 'itemCode')
            row['name'] = safe_get(item, 'name')
            row['categoryID'] = safe_get(item, 'categoryID')
            row['categoryName'] = safe_get(item, 'categoryName')
            row['description'] = safe_get(item, 'description')
            row['price'] = safe_get(item, 'price')
            row['stockInventory'] = safe_get(item, 'stockInventory')
            row['totalTaxes'] = safe_get(item, 'totalTaxes')
            row['totalFees'] = safe_get(item, 'totalFees')
            row['priceWithoutFeesAndTaxes'] = safe_get(item, 'priceWithoutFeesAndTaxes')
            row['grandTotal'] = safe_get(item, 'grandTotal')
            
            # Process taxes
            taxes = item.get('taxes', [])
            if isinstance(taxes, list) and taxes:
                for idx, tax in enumerate(taxes):
                    if tax is not None and isinstance(tax, dict):
                        num = idx + 1
                        row[f'tax_{num}_name'] = safe_get(tax, 'taxName')
                        row[f'tax_{num}_value'] = safe_get(tax, 'taxValue')
            
            # Process fees
            fees = item.get('fees', [])
            if isinstance(fees, list) and fees:
                for idx, fee in enumerate(fees):
                    if fee is not None and isinstance(fee, dict):
                        num = idx + 1
                        row[f'fee_{num}_name'] = safe_get(fee, 'feeName', safe_get(fee, 'name'))
                        row[f'fee_{num}_value'] = safe_get(fee, 'feeValue', safe_get(fee, 'value'))
            
            processed.append(row)
            print(f"✅ Processed item {i+1}: {row.get('name', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Error processing item {i}: {e}")
            continue
    
    print(f"📊 Total processed items: {len(processed)}")
    return processed

def process_taxes_fees_data(response):
    """Process taxes/fees API response"""
    if not response or not response.get('success'):
        return []
    
    data = response['data']
    items = []
    
    if isinstance(data, dict) and 'data' in data:
        items = data['data'] if isinstance(data['data'], list) else [data['data']]
    elif isinstance(data, list):
        items = data
    elif data is not None:
        items = [data]
    
    processed = []
    for item in items:
        if item is None:
            continue
        
        row = {}
        for key, value in item.items():
            if isinstance(value, (dict, list)):
                row[key] = str(value)  # Convert complex types to string
            else:
                row[key] = value
        processed.append(row)
    
    return processed

def process_rooms_data(room_types_response, rooms_response):
    """Process room types and rooms into hierarchical structure"""
    if not room_types_response or not room_types_response.get('success'):
        return []
    if not rooms_response or not rooms_response.get('success'):
        return []
    
    # Extract room types
    rt_data = room_types_response['data']
    room_types = []
    if isinstance(rt_data, dict) and 'data' in rt_data:
        room_types = rt_data['data'] if isinstance(rt_data['data'], list) else [rt_data['data']]
    elif isinstance(rt_data, list):
        room_types = rt_data
    
    # Extract rooms - handle the nested structure
    r_data = rooms_response['data']
    print(f"🔍 Raw rooms response structure: {type(r_data)}")
    
    rooms = []
    if isinstance(r_data, dict) and 'data' in r_data:
        rooms_data = r_data['data']
        print(f"🔍 Rooms data type: {type(rooms_data)}")
        
        if isinstance(rooms_data, list):
            # The API returns [{"propertyID": "6000", "rooms": [...]}]
            for property_data in rooms_data:
                if isinstance(property_data, dict) and 'rooms' in property_data:
                    property_rooms = property_data['rooms']
                    if isinstance(property_rooms, list):
                        rooms.extend(property_rooms)  # Extract the actual rooms array
                        print(f"🔍 Extracted {len(property_rooms)} rooms from property {property_data.get('propertyID')}")
    
    print(f"📊 Final count - Processing {len(room_types)} room types and {len(rooms)} individual rooms")
    
    # Show sample room data if available
    if rooms:
        sample_room = rooms[0]
        print(f"🔍 Sample room data: {sample_room}")
        if isinstance(sample_room, dict):
            print(f"🔍 Sample room keys: {list(sample_room.keys())}")
    
    processed = []
    
    for room_type in room_types:
        if room_type is None:
            continue
        
        room_type_id = safe_get(room_type, 'roomTypeID')
        room_type_name = safe_get(room_type, 'roomTypeName')
        
        print(f"🏨 Processing room type: {room_type_name} (ID: {room_type_id})")
        
        # Add room type row
        rt_row = {'data_type': 'Room Type'}
        for key, value in room_type.items():
            rt_row[f'roomtype_{key}'] = value
        rt_row['room_id'] = ''
        rt_row['room_name'] = ''
        processed.append(rt_row)
        
        # Find matching rooms - convert IDs to string for comparison
        matching_rooms = []
        for i, room in enumerate(rooms):
            if room is None:
                continue
            
            # Handle both string and integer room type IDs
            room_rt_id = safe_get(room, 'roomTypeID')
            room_name = safe_get(room, 'roomName')
            room_id = safe_get(room, 'roomID')
            
            # Convert both to strings for comparison (API might return integers)
            room_rt_id_str = str(room_rt_id)
            room_type_id_str = str(room_type_id)
            
            print(f"   Room {i}: {room_name} (ID: {room_id}) belongs to roomTypeID: {room_rt_id} (comparing {room_rt_id_str} vs {room_type_id_str})")
            
            if room_rt_id_str == room_type_id_str:
                matching_rooms.append(room)
                print(f"     ✅ MATCH! This room belongs to {room_type_name}")
            else:
                print(f"     ❌ No match - looking for {room_type_id_str}, found {room_rt_id_str}")
        
        print(f"   Found {len(matching_rooms)} rooms for room type {room_type_name}")
        
        # Add room rows
        for room in matching_rooms:
            r_row = {'data_type': 'Room'}
            # Add room type info for context
            for key, value in room_type.items():
                r_row[f'roomtype_{key}'] = value
            # Add room info
            for key, value in room.items():
                r_row[f'room_{key}'] = value
            processed.append(r_row)
            print(f"     + Added room: {safe_get(room, 'roomName')} (ID: {safe_get(room, 'roomID')})")
    
    print(f"📊 Total processed items: {len(processed)}")
    return processed

def get_all_columns(data_list):
    """Get all unique column names from processed data"""
    if not data_list:
        return []
    
    all_cols = set()
    for row in data_list:
        if isinstance(row, dict):
            all_cols.update(row.keys())
    
    # Sort with important columns first - propertyID should always be first
    priority_cols = ['propertyID', 'data_type', 'sourceID', 'sourceName', 'roomtype_roomTypeID', 'roomtype_roomTypeName', 'room_roomID', 'room_roomName']
    sorted_cols = []
    
    for col in priority_cols:
        if col in all_cols:
            sorted_cols.append(col)
            all_cols.remove(col)
    
    sorted_cols.extend(sorted(all_cols))
    return sorted_cols

def normalize_data(data_list, all_columns):
    """Ensure all rows have all columns"""
    for row in data_list:
        for col in all_columns:
            if col not in row:
                row[col] = ''
    return data_list

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/save-settings', methods=['POST'])
def save_settings():
    try:
        data = request.get_json()
        config = {
            'access_token': data.get('access_token', '').strip(),
            'property_id': data.get('property_id', '6000').strip()
        }
        save_config(config)
        return jsonify({'success': True, 'message': 'Settings saved successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/payment-methods')
def get_payment_methods():
    try:
        credentials = get_credentials()
        
        if not credentials['access_token']:
            return jsonify({'success': False, 'error': 'Access token not configured'})
        
        print(f"🚀 Fetching payment methods for property {credentials['property_id']}")
        
        response = make_api_call(PAYMENT_METHODS_URL, {'propertyID': credentials['property_id']}, credentials)
        
        if not response['success']:
            return jsonify({'success': False, 'error': response['error']})
        
        processed_data = process_payment_methods_data(response)
        all_columns = get_all_columns(processed_data)
        normalized_data = normalize_data(processed_data, all_columns)
        
        # Count gateways and payment methods
        gateway_count = len([r for r in processed_data if r.get('data_type') == 'Gateway'])
        payment_methods_count = len([r for r in processed_data if r.get('data_type') == 'Payment Method'])
        
        return jsonify({
            'success': True,
            'data': {
                'items': normalized_data,
                'columns': all_columns,
                'count': len(normalized_data),
                'gateway_count': gateway_count,
                'payment_methods_count': payment_methods_count
            }
        })
        
    except Exception as e:
        print(f"❌ Error in get_payment_methods: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/items')
def get_items():
    try:
        credentials = get_credentials()
        
        if not credentials['access_token']:
            return jsonify({'success': False, 'error': 'Access token not configured'})
        
        print(f"🚀 Fetching items for property {credentials['property_id']}")
        
        response = make_api_call(ITEMS_URL, {'propertyID': credentials['property_id']}, credentials)
        
        if not response['success']:
            return jsonify({'success': False, 'error': response['error']})
        
        processed_data = process_items_data(response)
        all_columns = get_all_columns(processed_data)
        normalized_data = normalize_data(processed_data, all_columns)
        
        return jsonify({
            'success': True,
            'data': {
                'items': normalized_data,
                'columns': all_columns,
                'count': len(normalized_data)
            }
        })
        
    except Exception as e:
        print(f"❌ Error in get_items: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get-settings')
def get_settings():
    return jsonify({'success': True, 'data': load_config()})

@app.route('/api/test-connection')
def test_connection():
    try:
        print("🔍 Test connection endpoint called")
        
        form_access_token = request.args.get('access_token')
        form_property_id = request.args.get('property_id')
        
        print(f"🔍 Form access token present: {bool(form_access_token)}")
        print(f"🔍 Form property ID: {form_property_id}")
        
        if form_access_token and form_property_id:
            credentials = {
                'access_token': form_access_token.strip(),
                'property_id': form_property_id.strip()
            }
        else:
            credentials = get_credentials()
            print(f"🔍 Using saved credentials - token present: {bool(credentials['access_token'])}")
        
        if not credentials['access_token']:
            return jsonify({'success': False, 'error': 'Please configure your access token first.'})
        
        print(f"🔍 Testing connection with property ID: {credentials['property_id']}")
        result = make_api_call(SOURCES_URL, {'propertyID': credentials['property_id']}, credentials)
        
        print(f"🔍 Test connection result: {result}")
        
        if result['success']:
            return jsonify({'success': True, 'message': 'Connection successful!'})
        else:
            return jsonify({'success': False, 'error': result['error']})
            
    except Exception as e:
        print(f"❌ Error in test_connection: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'})

@app.route('/api/sources')
def get_sources():
    try:
        credentials = get_credentials()
        
        if not credentials['access_token']:
            return jsonify({'success': False, 'error': 'Access token not configured'})
        
        # Support custom property ID from query parameter for bulk loading
        property_id = request.args.get('propertyID', credentials['property_id'])
        
        print(f"🚀 Fetching sources for property {property_id}")
        print(f"🔍 URL parameter propertyID: {request.args.get('propertyID')}")
        print(f"🔍 Using property_id: {property_id}")
        
        response = make_api_call(SOURCES_URL, {'propertyID': property_id}, credentials)
        
        if not response['success']:
            return jsonify({'success': False, 'error': response['error']})
        
        processed_data = process_sources_data(response)
        
        # FORCE set propertyID to the requested property_id for ALL rows
        for row in processed_data:
            row['propertyID'] = property_id
            print(f"🔍 Set propertyID to {property_id} for row")
        
        all_columns = get_all_columns(processed_data)
        normalized_data = normalize_data(processed_data, all_columns)
        
        print(f"🔍 Final data sample - first row propertyID: {normalized_data[0].get('propertyID') if normalized_data else 'No data'}")
        
        return jsonify({
            'success': True,
            'data': {
                'sources': normalized_data,
                'columns': all_columns,
                'count': len(normalized_data)
            }
        })
        
    except Exception as e:
        print(f"❌ Error in get_sources: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/taxes-fees')
def get_taxes_fees():
    try:
        credentials = get_credentials()
        
        if not credentials['access_token']:
            return jsonify({'success': False, 'error': 'Access token not configured'})
        
        # Support custom property ID from query parameter for bulk loading
        property_id = request.args.get('propertyID', credentials['property_id'])
        
        print(f"🚀 Fetching taxes/fees for property {property_id}")
        print(f"🔍 URL parameter propertyID: {request.args.get('propertyID')}")
        print(f"🔍 Using property_id: {property_id}")
        
        response = make_api_call(TAXES_FEES_URL, {'propertyID': property_id}, credentials)
        
        if not response['success']:
            return jsonify({'success': False, 'error': response['error']})
        
        processed_data = process_taxes_fees_data(response)
        
        # FORCE set propertyID to the requested property_id for ALL rows
        for row in processed_data:
            row['propertyID'] = property_id
            print(f"🔍 Set propertyID to {property_id} for row")
        
        all_columns = get_all_columns(processed_data)
        normalized_data = normalize_data(processed_data, all_columns)
        
        print(f"🔍 Final data sample - first row propertyID: {normalized_data[0].get('propertyID') if normalized_data else 'No data'}")
        
        return jsonify({
            'success': True,
            'data': {
                'items': normalized_data,
                'columns': all_columns,
                'count': len(normalized_data)
            }
        })
        
    except Exception as e:
        print(f"❌ Error in get_taxes_fees: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/rooms')
def get_rooms():
    try:
        credentials = get_credentials()
        
        if not credentials['access_token']:
            return jsonify({'success': False, 'error': 'Access token not configured'})
        
        print(f"🚀 Fetching rooms for property {credentials['property_id']}")
        
        # Get room types
        rt_response = make_api_call(ROOM_TYPES_URL, {'propertyID': credentials['property_id']}, credentials)
        if not rt_response['success']:
            return jsonify({'success': False, 'error': f"Room types: {rt_response['error']}"})
        
        # Get rooms
        r_response = make_api_call(ROOMS_URL, {'propertyID': credentials['property_id']}, credentials)
        if not r_response['success']:
            return jsonify({'success': False, 'error': f"Rooms: {r_response['error']}"})
        
        processed_data = process_rooms_data(rt_response, r_response)
        all_columns = get_all_columns(processed_data)
        normalized_data = normalize_data(processed_data, all_columns)
        
        # Count room types and rooms
        room_types_count = len([r for r in processed_data if r.get('data_type') == 'Room Type'])
        rooms_count = len([r for r in processed_data if r.get('data_type') == 'Room'])
        
        return jsonify({
            'success': True,
            'data': {
                'items': normalized_data,
                'columns': all_columns,
                'count': len(normalized_data),
                'room_types_count': room_types_count,
                'rooms_count': rooms_count
            }
        })
        
    except Exception as e:
        print(f"❌ Error in get_rooms: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/export/csv')
def export_csv():
    data_type = request.args.get('type', 'sources')
    credentials = get_credentials()
    
    if not credentials['access_token']:
        return "Access token not configured", 400
    
    try:
        if data_type == 'sources':
            # For sources, we need to handle both single property and bulk property exports
            bulk_property_ids = request.args.get('bulkPropertyIds', '')
            
            if bulk_property_ids:
                # Handle bulk export - load data for multiple properties
                property_ids = bulk_property_ids.split(',')
                all_data = []
                
                for prop_id in property_ids:
                    prop_id = prop_id.strip()
                    if prop_id:
                        response = make_api_call(SOURCES_URL, {'propertyID': prop_id}, credentials)
                        if response['success']:
                            prop_data = process_sources_data(response)
                            # Add propertyID to each row
                            for row in prop_data:
                                if 'propertyID' not in row or not row['propertyID']:
                                    row['propertyID'] = prop_id
                            all_data.extend(prop_data)
                
                # Sort by propertyID
                all_data.sort(key=lambda x: int(x.get('propertyID', 0)))
                data = all_data
            else:
                # Single property export
                response = make_api_call(SOURCES_URL, {'propertyID': credentials['property_id']}, credentials)
                if not response['success']:
                    return f"Error: {response['error']}", 500
                data = process_sources_data(response)
                # Add propertyID to each row for consistency
                for row in data:
                    if 'propertyID' not in row or not row['propertyID']:
                        row['propertyID'] = credentials['property_id']
            
            filename = f"cloudbeds_sources_{credentials['property_id']}"
            
        elif data_type == 'taxes-fees':
            # For taxes-fees, we need to handle both single property and bulk property exports
            # Check if we have bulk data in the frontend by looking for propertyID in the request
            bulk_property_ids = request.args.get('bulkPropertyIds', '')
            
            if bulk_property_ids:
                # Handle bulk export - load data for multiple properties
                property_ids = bulk_property_ids.split(',')
                all_data = []
                
                for prop_id in property_ids:
                    prop_id = prop_id.strip()
                    if prop_id:
                        response = make_api_call(TAXES_FEES_URL, {'propertyID': prop_id}, credentials)
                        if response['success']:
                            prop_data = process_taxes_fees_data(response)
                            # Add propertyID to each row
                            for row in prop_data:
                                row['propertyID'] = prop_id
                            all_data.extend(prop_data)
                
                # Sort by propertyID
                all_data.sort(key=lambda x: int(x.get('propertyID', 0)))
                data = all_data
            else:
                # Single property export
                response = make_api_call(TAXES_FEES_URL, {'propertyID': credentials['property_id']}, credentials)
                if not response['success']:
                    return f"Error: {response['error']}", 500
                data = process_taxes_fees_data(response)
                # Add propertyID to each row for consistency
                for row in data:
                    row['propertyID'] = credentials['property_id']
            
            filename = f"cloudbeds_taxes_fees_{credentials['property_id']}"
            
        elif data_type == 'payment-methods':
            response = make_api_call(PAYMENT_METHODS_URL, {'propertyID': credentials['property_id']}, credentials)
            if not response['success']:
                return f"Error: {response['error']}", 500
            data = process_payment_methods_data(response)
            filename = f"cloudbeds_payment_methods_{credentials['property_id']}"
            
        elif data_type == 'items':
            response = make_api_call(ITEMS_URL, {'propertyID': credentials['property_id']}, credentials)
            if not response['success']:
                return f"Error: {response['error']}", 500
            data = process_items_data(response)
            filename = f"cloudbeds_items_{credentials['property_id']}"
            
        elif data_type == 'rooms':
            rt_response = make_api_call(ROOM_TYPES_URL, {'propertyID': credentials['property_id']}, credentials)
            r_response = make_api_call(ROOMS_URL, {'propertyID': credentials['property_id']}, credentials)
            if not rt_response['success']:
                return f"Error: {rt_response['error']}", 500
            if not r_response['success']:
                return f"Error: {r_response['error']}", 500
            data = process_rooms_data(rt_response, r_response)
            filename = f"cloudbeds_rooms_{credentials['property_id']}"
            
        else:
            return "Invalid data type", 400
        
        if not data:
            return "No data to export", 404
        
        # Generate CSV
        all_columns = get_all_columns(data)
        normalized_data = normalize_data(data, all_columns)
        
        csv_rows = []
        csv_rows.append(','.join(f'"{col}"' for col in all_columns))
        
        for row in normalized_data:
            csv_row = []
            for col in all_columns:
                value = str(row.get(col, ''))
                value = value.replace('"', '""')  # Escape quotes
                csv_row.append(f'"{value}"')
            csv_rows.append(','.join(csv_row))
        
        csv_content = '\n'.join(csv_rows)
        
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        return f"Export error: {str(e)}", 500

def open_browser():
    time.sleep(2)
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    print("\n🏨 Cloudbeds Reports - Desktop App")
    print("=" * 50)
    print("📊 Starting server on http://localhost:5000")
    print("🌐 Opening browser automatically...")
    print("❌ Close this window to stop the application\n")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        app.run(host='127.0.0.1', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        input("Press Enter to close...")
        sys.exit(1)