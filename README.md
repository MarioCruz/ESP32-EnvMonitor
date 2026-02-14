# ESP32 EnvMonitor Display

Environmental monitoring dashboard on a 4.0" TFT display powered by an ESP32, running MicroPython. Displays CO2, temperature, and humidity readings in a clean 2x2 card layout.

Built to work with the [EnvMonitor](https://github.com/MarioCruz/EnvMonitor) project, porting the sensor dashboard from a web interface to a dedicated hardware display.

## Hardware

### Display Module: E32R40T / E32N40T (LCDWIKI)

- 4.0" TFT display, 320x480 resolution (used in landscape: 480x320)
- Driver IC: ST7796S
- Interface: 4-line SPI
- Color: 65K (RGB565)
- ESP32-32E module (ESP32-D0WD-V3, dual-core 240MHz)
- 4MB Flash, 520KB SRAM
- WiFi 2.4GHz 802.11 b/g/n
- Bluetooth 4.2
- Type-C for power and programming
- MicroSD card slot
- 3.7V lithium battery support with charging circuit
- RGB LED indicator
- Speaker output (1.5W @ 8Ω or 2W @ 4Ω)
- E32R40T model includes resistive touch screen (XPT2046)

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
| I2C SCL | 25 | For sensors (SCD4x, etc.) |
| I2C SDA | 32 | For sensors (SCD4x, etc.) |
| Audio Enable | 4 | Low = enable |
| Audio DAC | 26 | DAC output |
| Red LED | 22 | Common anode, low = on |
| Green LED | 16 | Common anode, low = on |
| Blue LED | 17 | Common anode, low = on |
| Battery ADC | 34 | Battery voltage (input only) |
| Input Only | 35, 39 | Expansion pins |
| BOOT Button | 0 | Download mode |
| UART TX | 1 | Serial |
| UART RX | 3 | Serial |

### Electrical Specs

| Parameter | Value |
|-----------|-------|
| Working Voltage | 5.0V (via Type-C) |
| Backlight Current | 142mA |
| Display Only Current | 230mA |
| Full Load Current | 580mA (display + speaker + charging) |
| Operating Temp | -10°C to 60°C |
| Battery Charging | 4.2-6.5V input, 290mA charge current |
| Battery Type | 3.7V polymer lithium |

## Software

### Requirements

- MicroPython v1.27.0+ on ESP32_GENERIC
- No additional libraries needed — pure MicroPython

### Files

| File | Description |
|------|-------------|
| `main.py` | Main loop — init display, read sensors, update dashboard |
| `display.py` | ST7796S driver, drawing primitives, dashboard UI |
| `font16.py` | 16x16 bitmap font with letters, numbers, symbols |

### Flashing

Copy files to the ESP32 using mpremote:

```bash
pip install mpremote
mpremote connect /dev/cu.usbserial-210 cp font16.py :font16.py
mpremote connect /dev/cu.usbserial-210 cp display.py :display.py
mpremote connect /dev/cu.usbserial-210 cp main.py :main.py
mpremote connect /dev/cu.usbserial-210 reset
```

### Sensor Integration (TODO)

Wire an SCD4x sensor to the I2C pins (GPIO 25 SCL, GPIO 32 SDA) and replace the mock data in `main.py` with real sensor reads.

## Links

- [EnvMonitor Web Dashboard (Pico W)](https://github.com/MarioCruz/EnvMonitor)
- [LCDWIKI E32R40T Documentation](http://www.lcdwiki.com)
- [MicroPython ESP32](https://micropython.org/download/ESP32_GENERIC/)
