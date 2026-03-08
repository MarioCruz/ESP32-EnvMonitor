"""
ESP32 EnvMonitor - Environmental Monitor with TFT Display
Reads CO2, temp, humidity, light from sensors
Displays on 4.0" ST7796S TFT in landscape
"""
import time
import gc
import machine
import ntptime
import display
import wifi
import sdlog
import audio
from config import WIFI_SSID, WIFI_PASSWORD, WIFI_NETWORKS, I2C_SCL_PIN, I2C_SDA_PIN, I2C_FREQUENCY, TIMEZONE_OFFSET, LOG_INTERVAL, TOUCH_ENABLED

print("[Main] ESP32 EnvMonitor starting...")

# Init display
display.init()

# === BOOT SEQUENCE ===
# Phase 1: Logo with line reveal
if display.show_logo("logo.bin"):
    time.sleep(2)

# Phase 2: Title screen with scan effect
display.boot_title()
time.sleep_ms(500)

# Phase 3: Init systems with progress bar
display.boot_progress(5, "Connecting WiFi...")
ip, wifi_ok = wifi.connect_multi(WIFI_NETWORKS)
if wifi_ok:
    display.boot_progress(25, "WiFi: " + ip, display.GREEN)
    print("[Main] WiFi:", ip)
else:
    display.boot_progress(25, "WiFi: Failed", display.RED)
    print("[Main] WiFi failed")
time.sleep_ms(400)

# NTP sync
ntp_ok = False
if wifi_ok:
    display.boot_progress(35, "Syncing time...")
    try:
        ntptime.host = "time.google.com"
        ntptime.settime()
        ntp_ok = True
        display.boot_progress(45, "NTP synced", display.GREEN)
        print("[Main] NTP synced")
    except Exception as e:
        display.boot_progress(45, "NTP failed", display.RED)
        print("[Main] NTP error:", e)
time.sleep_ms(400)

# SD Card
display.boot_progress(50, "Mounting SD card...")
sd_ok = sdlog.init()
if sd_ok:
    display.boot_progress(60, "SD card ready", display.GREEN)
else:
    display.boot_progress(60, "No SD card", display.RED)
time.sleep_ms(400)

# Init I2C + sensors
display.boot_progress(65, "Scanning sensors...")
sensor = None
light_sensor = None
sht = None
pressure_sensor = None

try:
    i2c = machine.I2C(0, scl=machine.Pin(I2C_SCL_PIN),
                       sda=machine.Pin(I2C_SDA_PIN),
                       freq=I2C_FREQUENCY)
    devices = i2c.scan()
    print("[Main] I2C devices:", [hex(d) for d in devices])

    if 0x62 in devices:
        display.boot_progress(70, "Init CO2 sensor...")
        from scd4x import SCD4X
        sensor = SCD4X(i2c)
        sensor.stop_periodic_measurement()
        time.sleep(1)
        sensor.start_periodic_measurement()
        print("[Main] SCD4x OK")
        time.sleep(2)

    if 0x10 in devices:
        display.boot_progress(80, "Init light sensor...")
        from veml7700 import VEML7700
        light_sensor = VEML7700(i2c)
        print("[Main] VEML7700 OK")

    if 0x44 in devices:
        display.boot_progress(85, "Init temp sensor...")
        from sht4x import SHT4X
        sht = SHT4X(i2c)
        print("[Main] SHT4x OK")

    if 0x60 in devices:
        display.boot_progress(90, "Init pressure sensor...")
        from mpl3115a2 import MPL3115A2
        pressure_sensor = MPL3115A2(i2c)
        print("[Main] MPL3115A2 OK")

except Exception as e:
    print("[Main] Sensor error:", e)

display.boot_progress(95, "Audio init...")
try:
    display.boot_progress(100, "Ready!", display.GREEN)
    audio.boot_melody()
except Exception as e:
    print("[Main] Audio error:", e)
    display.boot_progress(100, "Ready!", display.GREEN)
    time.sleep_ms(800)
display.fill_screen(display.BLACK)

# Touch screen
touch_mod = None
if TOUCH_ENABLED:
    try:
        import touch
        touch_mod = touch
        print("[Main] Touch enabled")
    except Exception as e:
        print("[Main] Touch init error:", e)

# RGB LED - common anode (low = on)
led_r = machine.Pin(22, machine.Pin.OUT, value=1)
led_g = machine.Pin(16, machine.Pin.OUT, value=1)
led_b = machine.Pin(17, machine.Pin.OUT, value=1)

# Battery ADC on GPIO34
batt_adc = machine.ADC(machine.Pin(34))
batt_adc.atten(machine.ADC.ATTN_11DB)  # Full range 0-3.3V

def read_battery_pct():
    """Read battery percentage from ADC. Returns -1 if no battery."""
    raw = batt_adc.read()
    # ESP32 ADC is 12-bit (0-4095), with voltage divider on board
    # Typical: 4.2V full = ~2.1V at ADC, 3.0V empty = ~1.5V at ADC
    # With 11dB atten, ~0-3.6V range
    voltage = raw / 4095 * 3.6 * 2  # x2 for voltage divider
    if voltage < 2.5:
        return -1  # No battery connected
    pct = int((voltage - 3.0) / (4.2 - 3.0) * 100)
    return max(0, min(100, pct))

def set_led(r, g, b):
    """Set RGB LED (1=on, 0=off). Inverted for common anode."""
    led_r.value(0 if r else 1)
    led_g.value(0 if g else 1)
    led_b.value(0 if b else 1)


def get_time_str():
    """Get formatted time string with timezone offset"""
    t = time.localtime(time.time() + TIMEZONE_OFFSET * 3600)
    h = t[3]
    ampm = "AM" if h < 12 else "PM"
    h12 = h % 12
    if h12 == 0:
        h12 = 12
    return "{:d}:{:02d} {}".format(h12, t[4], ampm)


def get_date_str():
    """Get formatted date string M-D-YY"""
    t = time.localtime(time.time() + TIMEZONE_OFFSET * 3600)
    return "{}-{}-{}".format(t[1], t[2], t[0] % 100)


# --- Touch zones (match dashboard card grid) ---
# Card grid: 3x3, card_w=152, card_h=78, gap=5
_card_w = 152
_card_h = 78
_gap = 5
_row1_y = 28
_row2_y = _row1_y + _card_h + _gap
_row3_y = _row2_y + _card_h + _gap
_x0 = (display.W - (3 * _card_w + 2 * _gap)) // 2

TOUCH_ZONES = {
    'co2':      (_x0, _row1_y, _card_w, _card_h),
    'temp':     (_x0 + _card_w + _gap, _row1_y, _card_w, _card_h),
    'humid':    (_x0 + 2 * (_card_w + _gap), _row1_y, _card_w, _card_h),
    'light':    (_x0, _row2_y, _card_w, _card_h),
    'air':      (_x0 + _card_w + _gap, _row2_y, _card_w, _card_h),
    'pressure': (_x0 + 2 * (_card_w + _gap), _row2_y, _card_w, _card_h),
    'sd':       (_x0, _row3_y, _card_w, _card_h),
    'wifi':     (_x0 + _card_w + _gap, _row3_y, _card_w, _card_h),
    'time':     (_x0 + 2 * (_card_w + _gap), _row3_y, _card_w, _card_h),
}

def _zone_hit(tx, ty):
    """Return which zone was tapped, or None."""
    for name, (zx, zy, zw, zh) in TOUCH_ZONES.items():
        if zx <= tx <= zx + zw and zy <= ty <= zy + zh:
            return name
    return None

touch_prev = False

# Alternate C/F each cycle
show_f = True
loop_count = 0
NTP_RESYNC_CYCLES = int(3600 / LOG_INTERVAL)  # resync every hour
WIFI_CHECK_CYCLES = int(60 / LOG_INTERVAL)    # check wifi every minute

# Main loop
print("[Main] Running...")
while True:
  try:
    # WiFi auto-reconnect
    if loop_count > 0 and loop_count % WIFI_CHECK_CYCLES == 0:
        if not wifi.is_connected():
            print("[Main] WiFi lost, reconnecting...")
            ip, wifi_ok = wifi.connect_multi(WIFI_NETWORKS)
            if wifi_ok:
                print("[Main] WiFi reconnected:", ip)

    # NTP resync periodically
    if wifi.is_connected() and loop_count > 0 and loop_count % NTP_RESYNC_CYCLES == 0:
        try:
            ntptime.settime()
            ntp_ok = True
            print("[Main] NTP resynced")
        except:
            pass

    co2 = 0
    temp_val = 0.0
    temp_c_log = 0.0
    hum = 0.0
    lux = 0
    pressure = 0.0
    status = wifi.get_ip() or "No WiFi"
    time_str = get_time_str() if ntp_ok else ""
    date_str = get_date_str() if ntp_ok else ""

    if sensor:
        try:
            if sensor.data_ready:
                co2 = sensor.CO2
                temp_c = sensor.temperature
                hum = sensor.relative_humidity
                temp_c_log = temp_c
                if show_f:
                    temp_val = temp_c * 9.0 / 5.0 + 32.0
                else:
                    temp_val = temp_c
        except Exception as e:
            print("[Main] SCD4x error:", e)

    # SHT4x as backup only if SCD4x didn't provide temp
    if sht and temp_c_log == 0.0:
        try:
            st, sh = sht.read()
            temp_c_log = st
            if show_f:
                temp_val = st * 9.0 / 5.0 + 32.0
            else:
                temp_val = st
            hum = sh
        except Exception as e:
            print("[Main] SHT4x error:", e)

    if light_sensor:
        try:
            lux = light_sensor.read_lux()
        except:
            try:
                lux = light_sensor.lux
            except Exception as e:
                print("[Main] Light error:", e)

    if pressure_sensor:
        try:
            pressure = pressure_sensor.pressure()
        except Exception as e:
            print("[Main] Pressure error:", e)

    unit = "F" if show_f else "C"
    print("[Data] CO2:{} T:{:.1f}{} H:{:.1f}% L:{}lux P:{:.0f}hPa {}".format(
        co2, temp_val, unit, hum, lux, pressure, time_str))
    display.draw_dashboard(co2, temp_val, hum, lux=lux, pressure=pressure,
                           sd_free=sdlog.free_space(),
                           status=status, unit_label=unit,
                           time_str=time_str, date_str=date_str,
                           batt_pct=read_battery_pct())
    if sd_ok and time_str:
        lt = time.localtime(time.time() + TIMEZONE_OFFSET * 3600)
        if not sdlog.log(date_str + " " + time_str, co2, temp_c_log, hum, lux, pressure, lt):
            print("[Main] SD log failed, remounting...")
            sd_ok = sdlog.init()
    # LED: green=good, yellow=fair, red=poor CO2
    if co2 > 0 and co2 < 1000:
        set_led(0, 1, 0)
    elif co2 >= 1000 and co2 < 1500:
        set_led(1, 1, 0)
    else:
        set_led(1, 0, 0)
    # Audio alerts
    try:
        if co2 >= 1500:
            audio.alert_tone()
        if hum >= 80:
            audio.beep(600, 200)
    except:
        pass
    # --- Touch input ---
    if touch_mod:
        touch_start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), touch_start) < (LOG_INTERVAL * 1000):
            try:
                pos = touch_mod.read()
            except:
                pos = None

            if pos is not None and not touch_prev:
                zone = _zone_hit(pos[0], pos[1])
                if zone:
                    print("[Touch] {} at ({},{})".format(zone, pos[0], pos[1]))

                if zone == 'temp':
                    # Toggle C/F and refresh immediately
                    show_f = not show_f
                    unit = "F" if show_f else "C"
                    if show_f:
                        temp_val = temp_c_log * 9.0 / 5.0 + 32.0
                    else:
                        temp_val = temp_c_log
                    display.draw_card(
                        TOUCH_ZONES['temp'][0], TOUCH_ZONES['temp'][1],
                        _card_w, _card_h,
                        "TEMP", "{:.1f}".format(temp_val), unit, display.ORANGE)
                    print("[Touch] Temp unit:", unit)

                elif zone == 'wifi':
                    # Show WiFi network details (reconnect if not connected)
                    if not wifi.is_connected():
                        display.draw_card(
                            TOUCH_ZONES['wifi'][0], TOUCH_ZONES['wifi'][1],
                            _card_w, _card_h,
                            "WIFI", "...", "connecting", display.YELLOW)
                        ip, wifi_ok = wifi.connect_multi(WIFI_NETWORKS)
                    ifcfg = wifi.wlan.ifconfig() if wifi.is_connected() else None
                    ox = _x0
                    oy = _row3_y
                    ow = 3 * _card_w + 2 * _gap
                    oh = _card_h
                    display.fill_rect(ox, oy, ow, oh, display.DKBLUE)
                    display.round_rect(ox, oy, ow, oh, display.CYAN, 2)
                    if ifcfg:
                        display.draw_text("IP: " + ifcfg[0], ox + 8, oy + 6, display.GREEN, display.DKBLUE, 1)
                        display.draw_text("GW: " + ifcfg[2], ox + 8, oy + 26, display.WHITE, display.DKBLUE, 1)
                        display.draw_text("DNS: " + ifcfg[3], ox + 8, oy + 46, display.WHITE, display.DKBLUE, 1)
                        display.draw_text("Mask: " + ifcfg[1], ox + 240, oy + 6, display.LTGRAY, display.DKBLUE, 1)
                        print("[Touch] WiFi IP:{} GW:{} DNS:{} Mask:{}".format(*ifcfg))
                    else:
                        display.draw_text("WiFi not connected", ox + 8, oy + 26, display.RED, display.DKBLUE, 1)
                        print("[Touch] WiFi not connected")

                elif zone == 'time':
                    # Show time details and NTP resync
                    synced = False
                    if wifi.is_connected():
                        try:
                            ntptime.settime()
                            ntp_ok = True
                            synced = True
                        except:
                            pass
                    ts = get_time_str() if ntp_ok else "--:--"
                    ds = get_date_str() if ntp_ok else "--"
                    utc_t = time.localtime()
                    utc_str = "{:02d}:{:02d} UTC".format(utc_t[3], utc_t[4])
                    ox = _x0
                    oy = _row3_y
                    ow = 3 * _card_w + 2 * _gap
                    oh = _card_h
                    display.fill_rect(ox, oy, ow, oh, display.DKBLUE)
                    display.round_rect(ox, oy, ow, oh, display.CYAN, 2)
                    display.draw_text("Time: " + ts, ox + 8, oy + 6, display.YELLOW, display.DKBLUE, 1)
                    display.draw_text("Date: " + ds, ox + 8, oy + 26, display.WHITE, display.DKBLUE, 1)
                    display.draw_text("UTC:  " + utc_str, ox + 8, oy + 46, display.LTGRAY, display.DKBLUE, 1)
                    ntp_str = "synced" if synced else "failed"
                    ntp_clr = display.GREEN if synced else display.RED
                    display.draw_text("NTP: " + ntp_str, ox + 240, oy + 6, ntp_clr, display.DKBLUE, 1)
                    display.draw_text("TZ: UTC{:+d}".format(TIMEZONE_OFFSET), ox + 240, oy + 26, display.LTGRAY, display.DKBLUE, 1)
                    uptime_s = time.ticks_ms() // 1000
                    up_h, up_m = divmod(uptime_s // 60, 60)
                    display.draw_text("Up: {}h {}m".format(up_h, up_m % 60), ox + 240, oy + 46, display.LTGRAY, display.DKBLUE, 1)
                    print("[Touch] Time:{} {} NTP:{}".format(ts, ds, ntp_str))

                elif zone == 'co2':
                    # Flash CO2 level detail
                    if co2 < 400:
                        msg, clr = "Outdoor", display.GREEN
                    elif co2 < 1000:
                        msg, clr = "Good", display.GREEN
                    elif co2 < 1500:
                        msg, clr = "Ventilate", display.YELLOW
                    elif co2 < 2000:
                        msg, clr = "Poor!", display.ORANGE
                    else:
                        msg, clr = "Danger!", display.RED
                    display.draw_card(
                        TOUCH_ZONES['co2'][0], TOUCH_ZONES['co2'][1],
                        _card_w, _card_h,
                        "CO2 " + str(co2), msg, "ppm", clr)
                    print("[Touch] CO2 detail:", msg)

                touch_prev = True
            elif pos is None:
                touch_prev = False

            time.sleep_ms(50)
    else:
        time.sleep(LOG_INTERVAL)

    show_f = not show_f
    loop_count += 1
    gc.collect()
  except Exception as e:
    print("[Main] Loop error:", e)

