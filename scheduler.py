import os
import sys
import subprocess
import signal
import time
from datetime import datetime, timedelta, time as dtime
from pytz import timezone
import requests

# Set up the virtual environment
venv_path = '/root/venv'
python_bin = os.path.join(venv_path, 'bin', 'python')
os.environ['PATH'] = os.path.join(venv_path, 'bin') + ':' + os.environ.get('PATH', '/usr/bin:/bin')
os.environ['VIRTUAL_ENV'] = venv_path

# Ensure the site-packages from the virtual environment are included
site_packages = os.path.join(venv_path, 'lib', 'python3.11', 'site-packages')
sys.path.insert(0, site_packages)

# Function to get sunrise and sunset times
def get_sun_times(latitude, longitude):
    url = f"https://api.sunrise-sunset.org/json?lat={latitude}&lng={longitude}&formatted=0"
    print(f"Requesting sunrise and sunset times from: {url}")
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    
    # Extract sunrise and sunset times in UTC
    sunrise_utc = datetime.fromisoformat(data['results']['sunrise']).time()
    sunset_utc = datetime.fromisoformat(data['results']['sunset']).time()
    
    # Convert times to the local time zone (America/New_York)
    ny_tz = timezone('America/New_York')
    sunrise_local = datetime.combine(datetime.utcnow(), sunrise_utc).replace(tzinfo=timezone('UTC')).astimezone(ny_tz).time()
    sunset_local = datetime.combine(datetime.utcnow(), sunset_utc).replace(tzinfo=timezone('UTC')).astimezone(ny_tz).time()
    
    print(f"Sunrise (local time): {sunrise_local}")
    print(f"Sunset (local time): {sunset_local}")
    
    return sunrise_local, sunset_local

# Function to check if current time is between two times
def is_time_between(start_time, end_time):
    current_time = datetime.now(timezone('America/New_York')).time()
    print(f"Current time: {current_time}")
    if start_time <= end_time:
        return start_time <= current_time <= end_time
    else:  # Over midnight
        return start_time <= current_time or current_time <= end_time

# Signal handler to terminate the script
def signal_handler(sig, frame):
    global process
    if process is not None:
        process.terminate()
        process = None
    print("Script terminated.")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Main function
def main():
    global process
    latitude = 40.682387
    longitude = -73.963004
    process = None
    
    while True:
        try:
            print("Checking sunrise and sunset times...")
            sunrise, _ = get_sun_times(latitude, longitude)
            end_time = dtime(22, 0)  # 10 PM local time
            
            if is_time_between(sunrise, end_time):
                if process is None:
                    # Start the script
                    process = subprocess.Popen([python_bin, "/root/rpi-rgb-led-matrix/display_text.py"])
                    print("Script started.")
                else:
                    print("Script is already running.")
            else:
                if process is not None:
                    # Stop the script
                    process.terminate()
                    process = None
                    print("Script stopped.")
                else:
                    print("Script is not running, waiting for sunrise.")
            
            time.sleep(60)  # Check every minute
        except requests.RequestException as e:
            print(f"Request error: {e}")
            time.sleep(60)  # Wait before retrying
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
