import os
import sys
import time
import signal
import subprocess
from datetime import datetime, time as dtime
import requests
from pytz import timezone

# Ensure psutil is installed
try:
    import psutil
except ImportError:
    os.system('pip install psutil')
    import psutil

# Path to the virtual environment and display_text.py script
venv_path = "/root/venv"
python_bin = os.path.join(venv_path, "bin", "python")
display_text_script = "/root/nycsubwayclock/display_text.py"

# Ensure the site-packages from the virtual environment are included
site_packages = os.path.join(venv_path, 'lib', 'python3.11', 'site-packages')
sys.path.insert(0, site_packages)

# Initialize process variable
process = None

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

# Function to check if a process is running
def is_process_running(script_name):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['cmdline']:  # Ensure cmdline is not None
            if script_name in proc.info['cmdline']:
                return True
    return False

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
                if not is_process_running("display_text.py"):
                    # Start the script
                    process = subprocess.Popen([python_bin, display_text_script])
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
