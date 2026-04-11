# NYC Subway Clock

Display real-time NYC subway arrival times on an LED matrix using a Raspberry Pi. Works with **all NYC subway lines** - just configure your station and go!

![NYC Subway Clock](https://img.shields.io/badge/platform-Raspberry%20Pi-red.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)

## Features

- Real-time subway arrival data from MTA GTFS feeds
- Supports **all NYC subway routes** with official MTA colors
- Programmatic route bullets rendered in each line's official color
- Direction-based display showing both directions simultaneously
- Efficient, lightweight code optimized for Raspberry Pi
- Easy configuration via `.env` file - no code editing required
- Stale cache fallback keeps the display running during brief network outages
- Graceful shutdown on SIGTERM (systemd-friendly) with display cleanup
- Comprehensive logging with rotation for 24/7 operation
- Automatic retry logic with exponential backoff
- Simulation mode for development without LED hardware

## Supported Routes

All NYC subway lines are supported with their official MTA colors:

| Color | Routes |
|-------|--------|
| Blue | A, C, E |
| Orange | B, D, F, M |
| Red | 1, 2, 3 |
| Green | 4, 5, 6 |
| Purple | 7 |
| Yellow | N, Q, R, W |
| Light Green | G |
| Brown | J, Z |
| Gray | L, S (shuttles) |

## Display Format

The display shows upcoming trains separated by direction:
- **Line 1**: Northbound trains (e.g., "Ma" + colored A bullet + "3m")
- **Line 2**: Southbound trains (e.g., "Bk" + colored F bullet + "2m")

Each route bullet is drawn as a filled circle in the route's official MTA color with a white letter inside.

Direction labels are customizable using 2-letter borough codes (Ma=Manhattan, Bk=Brooklyn, Qn=Queens, Bx=Bronx, Si=Staten Island). Use lowercase for the second letter.

## Hardware Requirements

- Raspberry Pi (tested on Pi 4B)
- RGB LED Matrix (this project uses 2 chained 32x64 matrices = 128x32 display)
- Adafruit RGB Matrix HAT or Bonnet
- 5V Power Supply for the LED matrices

## Project Structure

```
nycsubwayclock/
├── main.py                 # Main application entry point
├── config.py               # Configuration management with validation
├── .env.example            # Configuration template (copy to .env)
├── train_times/            # Subway data fetching module
│   ├── __init__.py
│   └── fetch.py            # GTFS feed processing with caching
├── display/                # LED matrix display module
│   ├── __init__.py
│   └── update.py           # Display rendering (DisplayManager class)
├── utils/                  # Utility functions
│   ├── __init__.py
│   └── helpers.py          # Helper functions
├── MTA.ttf                 # Custom MTA font
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

Copy the example configuration and customize it:

```bash
cp .env.example .env
```

Edit `.env` to set your station. At minimum, change these three settings:

```bash
# Your subway line
SUBWAY_ROUTE=C

# Your stop IDs (find in nyct-gtfs/nyct_gtfs/gtfs_static/stops.txt)
STOP_IDS=A44N,A44S

# Direction labels for your station
DIRECTION_NORTH_LABEL=Ma
DIRECTION_SOUTH_LABEL=Bk
```

### Finding Your Stop IDs

Stop IDs are in the GTFS static data at `nyct-gtfs/nyct_gtfs/gtfs_static/stops.txt`. Each station has IDs ending in `N` (northbound) and `S` (southbound).

Common examples:
- `A44N,A44S` = Clinton-Washington Avs (A/C line, Brooklyn)
- `A42N,A42S` = Hoyt-Schermerhorn (A/C/G lines)
- `635N,635S` = 14 St-Union Sq (4/5/6/N/Q/R/W lines)
- `725N,725S` = Times Sq-42 St (1/2/3 lines)
- `R20N,R20S` = DeKalb Av (B/D/F/M/N/Q/R/W lines)

You can search the file for your station name:
```bash
grep -i "your station name" nyct-gtfs/nyct_gtfs/gtfs_static/stops.txt
```

### 4. Run the Application

```bash
python main.py
```

Logs will be written to `logs/subway_clock.log`.

**For 24/7 operation:** See [RUNNING_CONTINUOUSLY.md](RUNNING_CONTINUOUSLY.md) for setting up auto-start on boot, monitoring, and maintenance recommendations.

### Development Without Hardware

You can develop and test without an LED matrix by enabling simulation mode:

```bash
SIMULATE_DISPLAY=true
```

This logs the display output instead of rendering to hardware.

## Configuration Options

All configuration is done through the `.env` file. See `.env.example` for full documentation.

| Setting | Description | Default |
|---------|-------------|---------|
| `SUBWAY_ROUTE` | Subway line to display (any NYC route) | C |
| `STOP_IDS` | Comma-separated stop IDs (northbound, southbound) | A44N,A44S |
| `MAX_TRAINS_PER_DIRECTION` | Maximum trains to show per direction | 3 |
| `MAX_MINUTES_AWAY` | Maximum minutes out to show (1-120) | 30 |
| `DIRECTION_NORTH_LABEL` | Label for northbound direction (2 letters) | Ma |
| `DIRECTION_SOUTH_LABEL` | Label for southbound direction (2 letters) | Bk |
| `DISPLAY_REFRESH_CYCLE` | Seconds between display refreshes | 5 |
| `CACHE_TTL_SECONDS` | How long to cache MTA feed data | 15 |
| `STALE_CACHE_MAX_SECONDS` | Max age of stale data to show during outages | 300 |
| `MATRIX_ROWS` | LED matrix rows | 32 |
| `MATRIX_COLS` | LED matrix columns | 64 |
| `MATRIX_CHAIN_LENGTH` | Number of chained panels | 2 |
| `MATRIX_GPIO_SLOWDOWN` | GPIO slowdown (4 for Pi 4, 3 for Pi 3) | 4 |
| `MATRIX_BRIGHTNESS` | Display brightness (0-100) | 50 |
| `SIMULATE_DISPLAY` | Run without hardware (true/false) | false |
| `FONT_PATH` | Path to font file | MTA.ttf |
| `FONT_SIZE` | Font size in pixels | 16 |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |

## Customization Examples

### Different Subway Lines

```bash
# 1/2/3 at Times Square
SUBWAY_ROUTE=1
STOP_IDS=725N,725S
DIRECTION_NORTH_LABEL=Up
DIRECTION_SOUTH_LABEL=Dt

# N/Q/R/W at Union Square
SUBWAY_ROUTE=N
STOP_IDS=635N,635S
DIRECTION_NORTH_LABEL=Up
DIRECTION_SOUTH_LABEL=Dt

# G train at Nassau Av
SUBWAY_ROUTE=G
STOP_IDS=G26N,G26S
DIRECTION_NORTH_LABEL=Qn
DIRECTION_SOUTH_LABEL=Bk
```

### Single Matrix Panel

If you're using just one 64x32 matrix:

```bash
MATRIX_CHAIN_LENGTH=1
```

### Different Raspberry Pi Model

```bash
# Pi 3 or older
MATRIX_GPIO_SLOWDOWN=3

# Pi 4
MATRIX_GPIO_SLOWDOWN=4
```

## Troubleshooting

### "No trains available"
- Check your `SUBWAY_ROUTE` matches your `STOP_IDS`
- Verify stop IDs are correct in `stops.txt`
- Check logs at `logs/subway_clock.log`
- Configuration is validated at startup - check for error messages

### Display flickering
- Try adjusting `MATRIX_GPIO_SLOWDOWN` (increase the value)
- Increase `MATRIX_PWM_LSB_NANOSECONDS` (e.g., 130)
- Ensure adequate power supply to LED matrices

### Import errors
- Make sure you cloned with `--recursive` flag
- Reinstall dependencies: `pip install -r requirements.txt`

### Permission errors on Raspberry Pi
- Run with sudo if needed: `sudo python main.py`
- Check file permissions

### Developing without hardware
- Set `SIMULATE_DISPLAY=true` in `.env` to log display output instead

## Credits & Acknowledgments

This project builds on the excellent work of others:

- **[nyct-gtfs](https://github.com/Andrew-Dickinson/nyct-gtfs)** by Andrew Dickinson - NYC Transit GTFS feed library
- **[rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix)** by Henner Zeller - RGB LED matrix driver
- **[MTA Countdown Clock Font](https://trmm.net/MTA_Countdown_Clock/)** by Trammell Hudson - Custom MTA font

Originally built with GitHub Copilot as a Christmas gift for my girlfriend. Refactored with Claude to make it more maintainable and accessible for others.

## Contributing

Feel free to open issues or submit pull requests! This project started as a learning experience, and improvements are always welcome.

## License

See [LICENSE](LICENSE) file for details.

---

**Built for New Yorkers, by a New Yorker.** Every apartment should have one of these!
