# ESP32 EnvMonitor TODO

## When Speaker Arrives (JST 1.25mm 2-pin, 8Ω)
- [ ] Plug speaker into board's speaker header
- [ ] Test basic beep: GPIO26 (DAC), GPIO4 (enable, low=on)
- [ ] Add boot-up melody (retro jingle)
- [ ] Add CO2 alert tone when crossing 1500 ppm
- [ ] Add configurable alert thresholds in config.py
- [ ] Consider different tones for different alerts (CO2 high, WiFi lost, etc.)

## Other
- [ ] Reformat SD card from Mac as FAT32 to get full 16GB
- [x] WiFi auto-reconnect if connection drops (checks every 60s)
- [x] NTP re-sync periodically (resyncs every hour)
- [x] CSV log file rotation (new file per day: envlog_YYMMDD.csv)
- [ ] Battery level card if running on LiPo (ADC on GPIO34)
