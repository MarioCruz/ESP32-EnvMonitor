# ESP32 EnvMonitor Display

Environmental monitoring dashboard on a 4.0" TFT display powered by an ESP32, running MicroPython. Displays CO2, temperature, humidity, light, air quality, and barometric pressure in a 3x3 card layout with SD card data logging.

Built to work with the [EnvMonitor](https://github.com/MarioCruz/EnvMonitor) project, porting the sensor dashboard from a web interface to a dedicated hardware display.

![MarioTheMaker](MarioTheMaker1.jpg)

## Features

- 3x3 dashboard with sensor cards (CO2, Temp C/F, Humidity, Light, Air Quality, Pressure, SD usage, WiFi status, Time/Date)
- Animated boot sequence with logo reveal, scan lines, progress bar
- SD card CSV data logging with daily file rotation (envlog_YYMMDD.csv)
- WiFi auto-reconnect (checks every 60s)
- NTP time sync with hourly resync
- RGB LED status indicator (green=good, yellow=fair, red=poor CO2)
- Temperature alternates between Celsius and Fahrenheit each refresh cycle
- SHT4x as backup temp/humidity sensor when SCD4x is unavailable
- Touchscreen support (E32R40T) — tap dashboard cards for interactive controls
- Audio alerts for high CO2 and humidity

## Hardware

### Display Module: E32R40T / E32N40T (LCDWIKI)

- 4.0" TFT display, 320x480 resolution (used in landscape: 480x320)
- Driver IC: ST7796S
- Interface: 4-line SPI
- Color: 65K (RGB565)
- ESP32-32E module (ESP32-D0WD-V3, dual-core 240MHz)
- 4MB Flash, 520KB SRAM
- WiFi 2.4GHz 802.11 b/g/n
- Type-C for power and programming
- MicroSD card slot
- 3.7V lithium battery support with charging circuit
- RGB LED indicator
- Speaker output (1.5W @ 8Ω or 2W @ 4Ω) via JST 1.25mm 2-pin connector
- E32R40T model includes resistive touch screen (XPT2046) — not present on E32N40T

### Sensors (I2C on GPIO25 SCL, GPIO32 SDA)

| Sensor | Address | Function |
|--------|---------|----------|
| SCD4x | 0x62 | CO2, temperature, humidity |
| SHT4x | 0x44 | Temperature, humidity (backup) |
| VEML7700 | 0x10 | Ambient light (lux) |
| MPL3115A2 | 0x60 | Barometric pressure (hPa) |

### Pin Mapping

| Function | GPIO | Notes |
|----------|------|-------|
| LCD CS | 15 | Chip select, active low |
| LCD DC | 2 | Data/Command select |
| LCD SCK | 14 | SPI clock (shared with touch) |
| LCD MOSI | 13 | SPI data out (shared with touch) |
| LCD MISO | 12 | SPI data in (shared with touch) |
| LCD Reset | EN | Shared with ESP32 reset |
| Backlight | 27 | High = on |
| Touch CS | 33 | Touch chip select (E32R40T only) |
| Touch IRQ | 36 | Touch interrupt (E32R40T only) |
| SD Card CS | 5 | MicroSD chip select |
| SD SCK | 18 | SD SPI clock |
| SD MOSI | 23 | SD SPI data out |
| SD MISO | 19 | SD SPI data in |
| I2C SCL | 25 | For sensors |
| I2C SDA | 32 | For sensors |
| Audio Enable | 4 | Low = enable |
| Audio DAC | 26 | DAC output |
| Red LED | 22 | Common anode, low = on |
| Green LED | 16 | Common anode, low = on |
| Blue LED | 17 | Common anode, low = on |
| Battery ADC | 34 | Battery voltage (input only) |

### Electrical Specs

| Parameter | Value |
|-----------|-------|
| Working Voltage | 5.0V (via Type-C) |
| Backlight Current | 142mA |
| Display Only Current | 230mA |
| Full Load Current | 580mA (display + speaker + charging) |
| Operating Temp | -10°C to 60°C |

## Software

### Requirements

- MicroPython v1.27.0+ on ESP32_GENERIC
- No additional libraries needed — pure MicroPython

### Files

| File | Description |
|------|-------------|
| `main.py` | Main loop — boot sequence, sensor reads, dashboard updates, SD logging |
| `display.py` | ST7796S driver, drawing primitives, boot animations, dashboard UI |
| `font16.py` | 16x16 bitmap font with letters, numbers, symbols |
| `wifi.py` | WiFi connection manager with auto-reconnect |
| `sdlog.py` | SD card CSV logger with daily file rotation |
| `sdcard.py` | MicroPython SD card SPI driver |
| `scd4x.py` | SCD4x CO2/temp/humidity sensor driver |
| `sht4x.py` | SHT4x temperature/humidity sensor driver (backup) |
| `veml7700.py` | VEML7700 ambient light sensor driver |
| `mpl3115a2.py` | MPL3115A2 barometric pressure sensor driver |
| `config.py` | WiFi credentials, I2C pins, timezone, logging interval (gitignored) |
| `touch.py` | XPT2046 resistive touch driver (E32R40T only) |
| `audio.py` | Speaker/audio driver (PWM on GPIO26, enable on GPIO4) |
| `config.example.py` | Template for config.py |
| `logo.bin` | Boot logo (320x320 RGB565 binary with 4-byte header) |
| `utils/test_touch.py` | Visual 4-corner touch calibration test |
| `utils/test_touch_raw.py` | Raw XPT2046 value debug tool for touch calibration |

### Setup

1. Flash MicroPython v1.27.0+ to your ESP32
2. Copy `config.example.py` to `config.py` and edit WiFi credentials
3. Copy all files to the ESP32:

```bash
pip install mpremote
mpremote connect /dev/cu.usbserial-210 cp config.py :config.py
mpremote connect /dev/cu.usbserial-210 cp main.py :main.py
mpremote connect /dev/cu.usbserial-210 cp display.py :display.py
mpremote connect /dev/cu.usbserial-210 cp font16.py :font16.py
mpremote connect /dev/cu.usbserial-210 cp wifi.py :wifi.py
mpremote connect /dev/cu.usbserial-210 cp sdlog.py :sdlog.py
mpremote connect /dev/cu.usbserial-210 cp sdcard.py :sdcard.py
mpremote connect /dev/cu.usbserial-210 cp scd4x.py :scd4x.py
mpremote connect /dev/cu.usbserial-210 cp sht4x.py :sht4x.py
mpremote connect /dev/cu.usbserial-210 cp veml7700.py :veml7700.py
mpremote connect /dev/cu.usbserial-210 cp mpl3115a2.py :mpl3115a2.py
mpremote connect /dev/cu.usbserial-210 cp touch.py :touch.py
mpremote connect /dev/cu.usbserial-210 cp audio.py :audio.py
mpremote connect /dev/cu.usbserial-210 cp logo.bin :logo.bin
mpremote connect /dev/cu.usbserial-210 mkdir :utils
mpremote connect /dev/cu.usbserial-210 cp utils/test_touch.py :utils/test_touch.py
mpremote connect /dev/cu.usbserial-210 cp utils/test_touch_raw.py :utils/test_touch_raw.py
mpremote connect /dev/cu.usbserial-210 reset
```

### Configuration (config.py)

```python
WIFI_SSID = "YourNetwork"
WIFI_PASSWORD = "YourPassword"
TIMEZONE_OFFSET = -5        # UTC offset in hours
LOG_INTERVAL = 5            # Seconds between readings
TOUCH_ENABLED = True        # Set False for E32N40T (no touch panel)
```

### SD Card Logging

Data is logged to CSV files on the SD card with daily rotation:
- Files named `envlog_YYMMDD.csv` (e.g. `envlog_260214.csv`)
- Columns: timestamp, co2, temp_c, humidity, lux, pressure_hpa
- Format SD card as FAT32 (MBR) for full capacity

### Touch Screen (E32R40T only)

The E32R40T board has an XPT2046 resistive touch controller sharing the SPI bus with the display. Enable it in `config.py`:

```python
TOUCH_ENABLED = True   # True for E32R40T, False for E32N40T
```

When enabled, tap dashboard cards for interactive controls:

| Card | Action |
|------|--------|
| **TEMP** | Toggle between Celsius and Fahrenheit |
| **CO2** | Show air quality detail (Good / Ventilate / Poor / Danger) |
| **WIFI** | Show network details — IP, gateway, DNS, subnet mask |
| **TIME** | NTP resync, show local time, UTC, timezone, uptime |

Touch info overlays appear on the bottom row and clear on the next sensor refresh.

### Utilities

Test scripts in the `utils/` directory for hardware validation:

```python
# Visual touch test — shows 4 boxes, tap each to confirm
from utils.test_touch import run
run()

# Raw touch debug — shows XPT2046 raw values for calibration
from utils.test_touch_raw import run
run()
```

If touch coordinates don't align with the screen, use `test_touch_raw.py` to read the raw values at each corner, then update the calibration constants in `touch.py`:

```python
# touch.py calibration (raw 12-bit XPT2046 values at screen edges)
X_MIN = 270    # raw value at right edge
X_MAX = 3850   # raw value at left edge
Y_MIN = 380    # raw value at bottom edge
Y_MAX = 3720   # raw value at top edge
```

## Links

- [EnvMonitor Web Dashboard (Pico W)](https://github.com/MarioCruz/EnvMonitor)
- [LCDWIKI E32R40T Documentation](https://www.lcdwiki.com/4.0inch_ESP32-32E_Display)
- [MicroPython ESP32](https://micropython.org/download/ESP32_GENERIC/)
- [GBE MicroPython Drivers](https://github.com/Growing-Beyond-Earth/gbe-micropython)
