# ESP32 EnvMonitor TODO

## Touch Screen
- [x] XPT2046 touch driver (touch.py) with calibrated coordinates
- [x] TOUCH_ENABLED config flag for E32R40T vs E32N40T
- [x] Tap TEMP card to toggle C/F
- [x] Tap CO2 card for air quality detail
- [x] Tap WIFI card to show IP, gateway, DNS, subnet
- [x] Tap TIME card for NTP resync, UTC, timezone, uptime
- [x] Touch calibration test utilities (utils/)
- [ ] Tap SD card to show log file info
- [ ] Tap LIGHT card to show min/max readings
- [ ] Tap PRESSURE card to show trend (rising/falling)

## Speaker (JST 1.25mm 2-pin, 8Ω)
- [x] Plug speaker into board's speaker header
- [x] Test basic beep: GPIO26 (PWM), GPIO4 (enable, low=on)
- [x] Add boot-up melody (retro riff)
- [x] Add CO2 alert tone when crossing 1500 ppm
- [ ] Add configurable alert thresholds in config.py
- [ ] Consider different tones for different alerts (CO2 high, WiFi lost, etc.)

## Other
- [ ] Reformat SD card from Mac as FAT32 to get full 16GB
- [x] WiFi auto-reconnect if connection drops (checks every 60s)
- [x] NTP re-sync periodically (resyncs every hour)
- [x] CSV log file rotation (new file per day: envlog_YYMMDD.csv)
- [x] Battery level gauge in dashboard title bar
- [ ] Battery level card if running on LiPo (ADC on GPIO34)
