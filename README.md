# NYC Subway Clock

Display real-time NYC subway arrival times on an LED matrix using a Raspberry Pi. Built as a Christmas gift, now available for all New Yorkers to enjoy!

![NYC Subway Clock](https://img.shields.io/badge/platform-Raspberry%20Pi-red.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)

## Features

- 🚇 Real-time subway arrival data from MTA GTFS feeds
- 🎨 Custom MTA font for authentic subway line bullets
- ⚡ Efficient, lightweight code optimized for Raspberry Pi
- 🔧 Easy configuration via `.env` file - no code editing required
- 📝 Comprehensive logging for debugging
- 🔄 Automatic retry logic with exponential backoff
- 📦 Clean, modular code structure

## Hardware Requirements

- Raspberry Pi (tested on Pi 4B)
- RGB LED Matrix (this project uses 2 chained 32x64 matrices = 128x32 display)
- Adafruit RGB Matrix HAT or Bonnet
- 5V Power Supply for the LED matrices

## Project Structure

```
nycsubwayclock/
├── main.py                 # Main application entry point
├── config.py               # Configuration management
├── .env                    # Configuration file (customize this!)
├── train_times/            # Subway data fetching module
│   ├── __init__.py
│   └── fetch.py            # GTFS feed processing
├── display/                # LED matrix display module
│   ├── __init__.py
│   └── update.py           # Display rendering (DisplayManager class)
├── utils/                  # Utility functions
│   ├── __init__.py
│   └── helpers.py          # Helper functions
├── MTA.ttf                 # Custom MTA font for subway bullets
├── nyct-gtfs/              # NYC Transit GTFS library (submodule)
└── rpi-rgb-led-matrix/     # RGB LED matrix library (submodule)
```

## Quick Start

### 1. Clone the Repository

```bash
git clone --recursive https://github.com/dustinniles/nycsubwayclock.git
cd nycsubwayclock
```

**Note**: The `--recursive` flag is important to pull the required submodules (nyct-gtfs and rpi-rgb-led-matrix).

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install RGB matrix library (follow their instructions)
cd rpi-rgb-led-matrix
make build-python
cd ..
```

### 3. Configure Your Display

Edit the `.env` file to customize for your setup:

```bash
# Subway Configuration - Change these for your stops!
SUBWAY_ROUTE=C                    # Your subway line (A, C, E, 1, 2, 3, etc.)
STOP_IDS=A44N,A44S                # Stop IDs (northbound, southbound)
MAX_TRAINS_DISPLAY=4              # How many trains to show
MAX_MINUTES_AWAY=30               # Max minutes out to display

# Display Timing
DISPLAY_REFRESH_INITIAL=3         # Seconds before first refresh
DISPLAY_REFRESH_CYCLE=5           # Seconds between display updates

# Matrix Hardware - Adjust for your LED matrix setup
MATRIX_ROWS=32                    # Rows per matrix panel
MATRIX_COLS=64                    # Columns per matrix panel
MATRIX_CHAIN_LENGTH=2             # Number of chained panels
MATRIX_GPIO_SLOWDOWN=3            # GPIO slowdown (4 for Pi 4B, 3 for Pi 3)
```

**Finding Your Stop IDs:**
Stop IDs can be found in the MTA GTFS data. For example:
- A44N/A44S = Clinton-Washington (C line, Brooklyn)
- Look up your stop in `nyct-gtfs/nyct_gtfs/gtfs_static/stops.txt`

### 4. Run the Application

```bash
python main.py
```

Logs will be written to `logs/subway_clock.log`.

## Configuration Options

All configuration is done through the `.env` file. Here are the available options:

| Setting | Description | Default |
|---------|-------------|---------|
| `SUBWAY_ROUTE` | Subway line to display (A, C, E, 1, 2, etc.) | C |
| `STOP_IDS` | Comma-separated stop IDs | A44N,A44S |
| `MAX_TRAINS_DISPLAY` | Number of trains to cycle through | 4 |
| `MAX_MINUTES_AWAY` | Maximum minutes out to show | 30 |
| `DISPLAY_REFRESH_INITIAL` | Initial display time (seconds) | 3 |
| `DISPLAY_REFRESH_CYCLE` | Cycle time between trains (seconds) | 5 |
| `MATRIX_ROWS` | LED matrix rows | 32 |
| `MATRIX_COLS` | LED matrix columns | 64 |
| `MATRIX_CHAIN_LENGTH` | Number of chained panels | 2 |
| `MATRIX_GPIO_SLOWDOWN` | GPIO slowdown (3-4 for Pi 3/4) | 3 |
| `FONT_PATH` | Path to MTA font file | MTA.ttf |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING) | INFO |

## Customization Examples

### Different Subway Line

To display the A train at your local stop:

```bash
SUBWAY_ROUTE=A
STOP_IDS=A42N,A42S  # Your stop IDs
```

### Single Matrix Panel

If you're using just one 64x32 matrix:

```bash
MATRIX_ROWS=32
MATRIX_COLS=64
MATRIX_CHAIN_LENGTH=1
```

### Different Raspberry Pi Model

For Raspberry Pi 3 or older:

```bash
MATRIX_GPIO_SLOWDOWN=3
```

For Raspberry Pi 4:

```bash
MATRIX_GPIO_SLOWDOWN=4
```

## Troubleshooting

### "No trains available"
- Check your `SUBWAY_ROUTE` matches your `STOP_IDS`
- Verify stop IDs are correct in `stops.txt`
- Check logs at `logs/subway_clock.log`

### Display flickering
- Try adjusting `MATRIX_GPIO_SLOWDOWN` (increase the value)
- Ensure adequate power supply to LED matrices

### Import errors
- Make sure you cloned with `--recursive` flag
- Reinstall dependencies: `pip install -r requirements.txt`

### Permission errors on Raspberry Pi
- Run with sudo if needed: `sudo python main.py`
- Check file permissions

## Credits & Acknowledgments

This project builds on the excellent work of others:

- **[nyct-gtfs](https://github.com/Andrew-Dickinson/nyct-gtfs)** by Andrew Dickinson - NYC Transit GTFS feed library
- **[rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix)** by Henner Zeller - RGB LED matrix driver
- **[MTA Countdown Clock Font](https://trmm.net/MTA_Countdown_Clock/)** by Trammell Hudson - Custom font where ACE bullets are represented by !@#

Originally built with GitHub Copilot as a Christmas gift for my girlfriend. Refactored with Claude to make it more maintainable and accessible for others.

## Contributing

Feel free to open issues or submit pull requests! This project started as a learning experience, and improvements are always welcome.

## License

See [LICENSE](LICENSE) file for details.

---

**Built for New Yorkers, by a New Yorker.** Every apartment should have one of these! 🗽🚇
