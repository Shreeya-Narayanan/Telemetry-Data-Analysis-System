# telemetry_simulator.py
# This script simulates various devices sending telemetry data to the FastAPI application.

import requests
import json
import time
import random
from datetime import datetime, timezone # Ensure timezone is imported

# --- Configuration ---
# The URL of your running FastAPI application's telemetry ingestion endpoint
FASTAPI_ENDPOINT = "http://127.0.0.1:8000/telemetry/"

# List of devices to simulate
DEVICES = [
    {"id": "sensor-alpha-001", "location": "Warehouse A"},
    {"id": "sensor-beta-002", "location": "Factory Floor"},
    {"id": "sensor-gamma-003", "location": "Office Building"},
    {"id": "sensor-delta-004", "location": "Data Center"}
]

# Define the types of metrics each device can send
# Each metric has a base value, a range for variation, and a unit
METRICS_CONFIG = {
    "temperature": {"base_value": 25.0, "variation_range": 5.0, "unit": "Celsius"},
    "humidity": {"base_value": 60.0, "variation_range": 10.0, "unit": "Percentage"},
    "cpu_usage": {"base_value": 40.0, "variation_range": 20.0, "unit": "Percentage"},
    "pressure": {"base_value": 1012.0, "variation_range": 5.0, "unit": "hPa"},
    "battery_level": {"base_value": 90.0, "variation_range": 5.0, "unit": "Percentage"}
}

# How often to send data (in seconds)
SEND_INTERVAL_SECONDS = 100.0

# --- Helper Function to Generate Telemetry Data ---
def generate_telemetry_payload(device_info):
    """
    Generates a single JSON payload for a telemetry event.
    """
    device_id = device_info["id"]
    
    # Randomly pick a metric to send for this device
    metric_name = random.choice(list(METRICS_CONFIG.keys()))
    metric_config = METRICS_CONFIG[metric_name]

    # Generate a metric value with some random variation
    metric_value = metric_config["base_value"] + random.uniform(-metric_config["variation_range"]/2, metric_config["variation_range"]/2)
    metric_value = round(metric_value, 2) # Round to 2 decimal places

    # Get current UTC timestamp in ISO 8601 format
    # FIX: Use timezone-aware datetime.now(timezone.utc) instead of utcnow()
    timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

    payload = {
        "timestamp": timestamp,
        "device_id": device_id,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "unit": metric_config["unit"]
    }
    return payload

# --- Main Simulation Loop ---
def start_simulation():
    """
    Starts the continuous simulation of telemetry data sending.
    """
    print(f"Starting telemetry data simulation. Sending data every {SEND_INTERVAL_SECONDS} seconds...")
    print(f"Sending to: {FASTAPI_ENDPOINT}")

    try:
        while True:
            # Randomly pick a device to send data from
            device = random.choice(DEVICES)
            payload = generate_telemetry_payload(device)

            try:
                # Send the POST request
                response = requests.post(FASTAPI_ENDPOINT, json=payload)
                response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

                # Print success message
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Sent data for device '{payload['device_id']}', metric '{payload['metric_name']}' (Value: {payload['metric_value']} {payload['unit']}). Status: {response.status_code}")

            except requests.exceptions.ConnectionError as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Could not connect to FastAPI app. Is it running at {FASTAPI_ENDPOINT}? Error: {e}")
            except requests.exceptions.HTTPError as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: HTTP error occurred: {e}. Response: {response.text}")
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] An unexpected error occurred: {e}")

            time.sleep(SEND_INTERVAL_SECONDS) # Wait before sending the next data point

    except KeyboardInterrupt:
        print("\nSimulation stopped by user (Ctrl+C).")
    except Exception as e:
        print(f"An error occurred during simulation: {e}")

if __name__ == "__main__":
    start_simulation()
