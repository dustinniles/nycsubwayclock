# nycsubwayclock
This project is designed to display NYC subway information on an LED matrix using a Raspberry Pi.

## Project Structure

- **nyct-gtfs**: [Andrew Dickinson's nyct-gtfs](https://github.com/Andrew-Dickinson/nyct-gtfs.git) repository.
- **rpi-rgb-led-matrix**: [Henner Zeller's rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix) repository.
- **Your Project Files**: Custom scripts and configurations for displaying subway information on an LED matrix.

## Setup Instructions

1. Clone this repository to your Raspberry Pi:
   ```sh
   git clone --recursive git@github.com:your-username/nycsubwayclock.git
   cd nycsubwayclock

2. Edit display_text.py and scheduler.py
     display_text.py actually queries the information and displays it on the screen. Edit the feeds for the subway line you need and the stops you want to display (mine are set to the 'C' line and 'A44N' & 'A44S' (Clinton-Washington stop).
     scheduler.py simply uses a date and time API to check every minute if it's between sunrise and 10PM and runs displaytext.py if so. You can probably leave the coordinates the same but you'll need to customize for when you want the screen to go on and off.

3. See the subdirectories for more info.
