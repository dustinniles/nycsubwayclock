"""
This script manages the execution of the display_text.py script based on the
sunrise and sunset times in New York City. It ensures that only one instance
of display_text.py is running at any given time using a lock file mechanism.
"""

import os
import sys
import time
import signal
import subprocess
from datetime import datetime, time as dtime
import requests
from pytz import timezone
import psutil

# Path to the virtual environment and display_text.py script
venv_path = "/root/venv"
python_bin = os.path.join(venv_path, "bin", "python")
display_text_script = "/root/nycsubwayclock/display_text.py"
lock_file_path = "/tmp/display_text.lock"

# Ensure the site-packages from the virtual environment are included
site_packages = os.path.join(venv_path, "lib", "python3.11", "site-packages")
sys.path.insert(0, site_packages)

# Initialize process variable
process = None


def get_sun_times(latitude, longitude):
    """
    Retrieves sunrise and sunset times for a given latitude and longitude. Right now it's a random spot in BK newar Prospect Park.
    I can't imagine if you're interested in the NYC Subway that your subrise.sunset would be meaningfully different, but if you want to be exact,
    feel free to change it.

    Args:
        latitude (float): The latitude of the location.
        longitude (float): The longitude of the location.

    Returns:
        tuple: A tuple containing the local sunrise and sunset times as datetime.time objects.
    """
    url = f"https://api.sunrise-sunset.org/json?lat={latitude}&lng={longitude}&formatted=0"
    print(f"Requesting sunrise and sunset times from: {url}")
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    # Extract sunrise and sunset times in UTC
    sunrise_utc = datetime.fromisoformat(data["results"]["sunrise"]).time()
    sunset_utc = datetime.fromisoformat(data["results"]["sunset"]).time()

    # Convert times to the local time zone (America/New_York)
    ny_tz = timezone("America/New_York")
    sunrise_local = (
        datetime.combine(datetime.utcnow(), sunrise_utc)
        .replace(tzinfo=timezone("UTC"))
        .astimezone(ny_tz)
        .time()
    )
    sunset_local = (
        datetime.combine(datetime.utcnow(), sunset_utc)
        .replace(tzinfo=timezone("UTC"))
        .astimezone(ny_tz)
        .time()
    )

    print(f"Sunrise (local time): {sunrise_local}")
    print(f"Sunset (local time): {sunset_local}")

    return sunrise_local, sunset_local


def is_time_between(start_time, end_time):
    """
    Checks if the current time is between the specified start and end times.

    Args:
        start_time (datetime.time): The start time.
        end_time (datetime.time): The end time.

    Returns:
        bool: True if the current time is between start_time and end_time, False otherwise.
    """
    current_time = datetime.now(timezone("America/New_York")).time()
    print(f"Current time: {current_time}")
    if start_time <= end_time:
        return start_time <= current_time <= end_time
    else:  # Over midnight
        return start_time <= current_time or current_time <= end_time


def is_process_running(script_name):
    """
    Checks if a process with the given script name is currently running.

    Args:
        script_name (str): The name of the script to check.

    Returns:
        bool: True if the process is running, False otherwise.
    """
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        if proc.info["cmdline"] and script_name in proc.info["cmdline"]:
            return True
    return False


def create_lock_file():
    """
    Creates a lock file to indicate that the display_text.py script is running.
    """
    with open(lock_file_path, "w") as lock_file:
        lock_file.write(str(os.getpid()))


def remove_lock_file():
    """
    Removes the lock file to indicate that the display_text.py script has stopped.
    """
    if os.path.exists(lock_file_path):
        os.remove(lock_file_path)


def signal_handler(sig, frame):
    """
    Handles termination signals to gracefully stop the script and clean up resources.

    Args:
        sig (int): The signal number.
        frame (frame object): The current stack frame.
    """
    global process
    remove_lock_file()
    if process is not None:
        process.terminate()
        process = None
    print("Script terminated.")
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def main():
    """
    The main function that controls the execution of the display_text.py script
    based on sunrise and sunset times in New York City. It ensures that only one
    instance of display_text.py is running at any given time using a lock file mechanism.
    """
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
                if not os.path.exists(lock_file_path):
                    # Start the script and create a lock file
                    process = subprocess.Popen([python_bin, display_text_script])
                    create_lock_file()
                    print("Script started.")
                else:
                    print("Script is already running.")
            else:
                if process is not None:
                    # Stop the script and remove the lock file
                    process.terminate()
                    process = None
                    remove_lock_file()
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
