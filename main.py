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
from config import WIFI_SSID, WIFI_PASSWORD, I2C_SCL_PIN, I2C_SDA_PIN, I2C_FREQUENCY, TIMEZONE_OFFSET, LOG_INTERVAL

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
ip, wifi_ok = wifi.connect(WIFI_SSID, WIFI_PASSWORD)
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

display.boot_progress(100, "Ready!", display.GREEN)
time.sleep_ms(800)
display.fill_screen(display.BLACK)

# RGB LED - common anode (low = on)
led_r = machine.Pin(22, machine.Pin.OUT, value=1)
led_g = machine.Pin(16, machine.Pin.OUT, value=1)
led_b = machine.Pin(17, machine.Pin.OUT, value=1)

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
            ip, wifi_ok = wifi.connect(WIFI_SSID, WIFI_PASSWORD)
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
                           time_str=time_str, date_str=date_str)
    if sd_ok and time_str:
        lt = time.localtime(time.time() + TIMEZONE_OFFSET * 3600)
        sdlog.log(date_str + " " + time_str, co2, temp_c_log, hum, lux, pressure, lt)
    # LED: green=good, yellow=fair, red=poor CO2
    if co2 > 0 and co2 < 1000:
        set_led(0, 1, 0)
    elif co2 >= 1000 and co2 < 1500:
        set_led(1, 1, 0)
    else:
        set_led(1, 0, 0)
    show_f = not show_f
    loop_count += 1
    gc.collect()
  except Exception as e:
    print("[Main] Loop error:", e)
  time.sleep(LOG_INTERVAL)
