# nycsubwayclock
This project is designed to display NYC subway information on an LED matrix using a Raspberry Pi.

## Project Structure

- **nyct-gtfs**: [Andrew Dickinson's nyct-gtfs](https://github.com/Andrew-Dickinson/nyct-gtfs.git) repository.
- **rpi-rgb-led-matrix**: [Henner Zeller's rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix) repository.
- **train_time,display, and util directories**: Python files that work together to pull traintimes and display them on the matrix.
- **Main.py**: Main file that pulls together from above directories
- **Font**: MTA.ttf from [Trammell Hudson's MTA Countdown Clock Project](https://trmm.net/MTA_Countdown_Clock/), customized so ACE bullets are represented by !@#.

## Setup Instructions

1. Clone this repository to your Raspberry Pi:
   ```sh
   git clone --recursive git@github.com:dustinniles/nycsubwayclock.git
   cd nycsubwayclock

2. Edit necessary files
   Edit train_time files to pull from the feeds for the subway line you need and the stops you want to display (mine are set to the 'C' line and 'A44N' & 'A44S' (Clinton-Washington stop). Usually local/express trios are combined into the same feed.
     scheduler.py simply uses a date and time API to check every minute if it's between sunrise and 10PM and runs the display function if so. You can probably leave the coordinates the same (it's just a spot in BK near Prospect Park, I imagine most New Yorkers sunrise/sunset times are about the same but feel free to edit if you want to be exact for fun) but you'll need to customize for when you want the screen to go on and off.

4. See the subdirectories for more info. For instance, the display files are set for a GPIO slowdown for a Raspebrry Pi 4B, and set for 2 chained 32x64 LED matrices. You may need different settings.


## NOTE

I know absolute diddly squat about coding. Really, nothing. GitHub Copilot wrote 99% of this. If you've got tips, tricks, suggestions, etc. I'm all ears. I'm still running into some slight flickering issues, and will update the code if I find a cure. But I wanted to put the code up so that someone like me, who knows nothing, could get this up and running (hopefully) fairly painlessly. I built this as a Christmas gift for my girlfriend, but I feel like every New Yorker should have one of these in their homes.
