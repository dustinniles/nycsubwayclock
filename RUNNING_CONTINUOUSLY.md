# Running the NYC Subway Clock Continuously

This document covers important considerations for running the subway clock 24/7 on your Raspberry Pi.

## ✅ Already Handled

The code includes several features specifically for continuous operation:

### 1. **Log Rotation** ✅
- Logs automatically rotate when they reach 10MB
- Keeps the last 5 log files (50MB total maximum)
- Prevents your SD card from filling up over time
- Configurable via `.env`: `LOG_MAX_BYTES` and `LOG_BACKUP_COUNT`

### 2. **Automatic Error Recovery** ✅
- API failures retry automatically with exponential backoff (2, 4, 8 seconds)
- Main loop catches exceptions and continues running
- 10-second delay before retrying after unexpected errors

### 3. **Memory Management** ✅
- No memory leaks - objects are reused, not recreated in loops
- DisplayManager created once at startup
- Image buffers reused for each frame

### 4. **Graceful Shutdown** ✅
- Handles Ctrl+C (KeyboardInterrupt) cleanly
- Logs shutdown message

## 🔧 Recommended: Auto-Start on Boot

To make the subway clock start automatically when your Raspberry Pi boots up, use systemd:

### Create a systemd service

1. Create the service file:
```bash
sudo nano /etc/systemd/system/subway-clock.service
```

2. Add this content (adjust paths as needed):
```ini
[Unit]
Description=NYC Subway Clock
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/nycsubwayclock
ExecStart=/home/pi/nycsubwayclock/venv/bin/python /home/pi/nycsubwayclock/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable subway-clock.service
sudo systemctl start subway-clock.service
```

4. Check status:
```bash
sudo systemctl status subway-clock.service
```

5. View logs:
```bash
sudo journalctl -u subway-clock.service -f
```

### Service Management Commands

```bash
# Stop the service
sudo systemctl stop subway-clock.service

# Restart the service
sudo systemctl restart subway-clock.service

# Disable auto-start
sudo systemctl disable subway-clock.service

# View recent logs
sudo journalctl -u subway-clock.service -n 50
```

## 📊 Monitoring

### Check if it's running:
```bash
ps aux | grep main.py
```

### Monitor resource usage:
```bash
# CPU and memory usage
top -p $(pgrep -f main.py)

# Or use htop (install with: sudo apt install htop)
htop
```

### Check log file size:
```bash
ls -lh logs/
```

## ⚠️ Things to Watch For

### 1. **Network Connectivity**
The app needs internet to fetch train data. If your WiFi drops:
- The retry logic will attempt to reconnect
- After 3 failed attempts, it returns empty data
- Display shows "No trains available"
- It will retry on the next cycle

**Solution**: Ensure stable WiFi connection. Consider using ethernet cable for more reliability.

### 2. **MTA API Changes**
The MTA occasionally updates their GTFS feeds or API structure.

**Signs of problems:**
- Consistently showing "No trains available"
- Error messages about feed parsing

**Solution**: Check the logs at `logs/subway_clock.log` and update the `nyct-gtfs` library:
```bash
cd nyct-gtfs
git pull
cd ..
```

### 3. **Power Supply**
LED matrices draw significant power. Insufficient power can cause:
- Display flickering
- Raspberry Pi crashes/reboots
- SD card corruption

**Solution**: Use a proper 5V power supply rated for your LED matrix (typically 5V 4A or higher for dual panels).

### 4. **SD Card Health**
Continuous writing (logs, even with rotation) can wear out SD cards over time.

**Best practices:**
- Use a high-quality SD card (Class 10, A1 or A2 rated)
- Consider reducing log level to WARNING in production: `LOG_LEVEL=WARNING`
- Backup your SD card periodically

### 5. **GTFS Static Files**
The app reads `trips.txt` and `stops.txt` once at startup. If the MTA updates these files:
- Your train times will still work (they come from real-time feed)
- But if stop IDs change, you might see incorrect data

**Solution**: Restart the app occasionally (weekly/monthly) or after MTA announces schedule changes.

## 🔄 Recommended Maintenance

### Weekly:
- Check that display is showing correct train times
- Glance at log file size: `ls -lh logs/`

### Monthly:
- Check for updates to `nyct-gtfs` library
- Review logs for any recurring errors
- Verify SD card has adequate free space: `df -h`

### After MTA Schedule Changes:
- Restart the service: `sudo systemctl restart subway-clock.service`
- This reloads the GTFS static files with updated schedules

## 🐛 Troubleshooting Continuous Operation

### App stops after a while
- Check logs: `tail -n 100 logs/subway_clock.log`
- Check system logs: `sudo journalctl -xe`
- Verify power supply is adequate
- Check for SD card errors: `dmesg | grep mmc`

### Display freezes but app is running
- May be a display hardware issue
- Try restarting: `sudo systemctl restart subway-clock.service`
- Check power supply to LED matrices

### High CPU usage
- Check if multiple instances are running: `ps aux | grep main.py`
- Only one instance should be running
- If multiple, kill extras: `sudo pkill -f main.py` then restart service

### Logs growing too fast
- Reduce log level: Set `LOG_LEVEL=WARNING` in `.env`
- Reduce log file size: Set `LOG_MAX_BYTES=5242880` (5MB) in `.env`
- Reduce backup count: Set `LOG_BACKUP_COUNT=3` in `.env`

## 💡 Performance Tips

1. **Reduce Logging in Production**:
   ```bash
   LOG_LEVEL=WARNING
   ```
   This significantly reduces log writes while still capturing errors.

2. **Use Ethernet Instead of WiFi**:
   More stable connection = fewer retries = better performance.

3. **Overclock Carefully**:
   If display is slow, consider modest Raspberry Pi overclock, but ensure adequate cooling.

4. **Monitor Temperature**:
   ```bash
   vcgencmd measure_temp
   ```
   Keep it under 80°C. Add heatsinks or fan if needed.

## 📝 Example: Full Setup for 24/7 Operation

```bash
# 1. Set production logging
echo "LOG_LEVEL=WARNING" >> .env

# 2. Create systemd service
sudo nano /etc/systemd/system/subway-clock.service
# (paste service configuration from above)

# 3. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable subway-clock.service
sudo systemctl start subway-clock.service

# 4. Verify it's running
sudo systemctl status subway-clock.service

# 5. Set up weekly restart (optional but recommended)
# This reloads GTFS data and clears any accumulated state
sudo crontab -e
# Add this line:
0 3 * * 0 /bin/systemctl restart subway-clock.service
```

That's it! Your subway clock will now run continuously, start on boot, and handle errors gracefully.
