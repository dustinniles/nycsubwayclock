# nycsubwayclock
This project is designed to display NYC subway information on an LED matrix using a Raspberry Pi.

## Project Structure

- **nyct-gtfs**: [Andrew Dickinson's nyct-gtfs](https://github.com/Andrew-Dickinson/nyct-gtfs.git) repository.
- **rpi-rgb-led-matrix**: [Henner Zeller's rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix) repository.
- **display_text.py and scheduler.py**: Custom scripts and configurations for displaying subway information on an LED matrix and turning on and off based on the time.
- **Font**: MTA.ttf from [Trammell Hudson's MTA Countdown Clock Project](https://trmm.net/MTA_Countdown_Clock/), customized so ACE bullets are represented as !@#.

## Setup Instructions

1. Clone this repository to your Raspberry Pi:
   ```sh
   git clone --recursive git@github.com:dustinniles/nycsubwayclock.git
   cd nycsubwayclock

2. Edit display_text.py and scheduler.py
   display_text.py actually queries the information and displays it on the screen. Edit the feeds for the subway line you need and the stops you want to display (mine are set to the 'C' line and 'A44N' & 'A44S' (Clinton-Washington stop).
     scheduler.py simply uses a date and time API to check every minute if it's between sunrise and 10PM and runs displaytext.py if so. You can probably leave the coordinates the same but you'll need to customize for when you want the screen to go on and off.

4. See the subdirectories for more info. For instance, display_text.py is set for a GPIO slowdown for a Raspebrry Pi 4, and set for 2 chained 32x64 LED matrices. You may need different settings.


##NOTE
I know absolute diddly squat about coding. Really, nothing. GitHub Copilot wrote 99% of this. If you've got tips, tricks, suggestions, etc. I'm all ears. I'm still running into some slight flickering issues, and will update the code if I find a cure. But I wanted to put the code up so that someone like me, who knows nothing, could get this up and running (hopefully) fairly painlessly. I built this as a Christmas gift for my girlfriend, but I feel like every New Yorker should have one of these in their homes.
