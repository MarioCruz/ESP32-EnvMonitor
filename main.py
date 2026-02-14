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
display.fill_screen(display.BLACK)

# Show boot logo
if display.show_logo("logo.bin"):
    time.sleep(3)

display.fill_screen(display.BLACK)
display.draw_text("EnvMonitor", 120, 60, display.CYAN, display.BLACK, 2)
display.draw_text("Starting...", 120, 110, display.GRAY, display.BLACK, 1)

# Connect WiFi
display.draw_text("WiFi...", 120, 140, display.YELLOW, display.BLACK, 1)
ip, wifi_ok = wifi.connect(WIFI_SSID, WIFI_PASSWORD)
if wifi_ok:
    display.draw_text(ip, 120, 170, display.GREEN, display.BLACK, 1)
    print("[Main] WiFi:", ip)
else:
    display.draw_text("No WiFi", 120, 170, display.RED, display.BLACK, 1)
    print("[Main] WiFi failed")
time.sleep(1)

# Sync NTP time
ntp_ok = False
if wifi_ok:
    display.draw_text("NTP sync...", 120, 200, display.YELLOW, display.BLACK, 1)
    try:
        ntptime.host = "time.google.com"
        ntptime.settime()
        ntp_ok = True
        print("[Main] NTP synced")
    except Exception as e:
        print("[Main] NTP error:", e)
time.sleep(1)

# Init SD card
display.draw_text("SD Card...", 120, 230, display.YELLOW, display.BLACK, 1)
sd_ok = sdlog.init()
if sd_ok:
    display.draw_text("SD OK", 120, 250, display.GREEN, display.BLACK, 1)
else:
    display.draw_text("No SD", 120, 250, display.RED, display.BLACK, 1)

# Init I2C + sensors
display.draw_text("Sensors...", 120, 270, display.YELLOW, display.BLACK, 1)
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
        from scd4x import SCD4X
        sensor = SCD4X(i2c)
        sensor.stop_periodic_measurement()
        time.sleep(1)
        sensor.start_periodic_measurement()
        print("[Main] SCD4x OK")
        time.sleep(2)

    if 0x10 in devices:
        from veml7700 import VEML7700
        light_sensor = VEML7700(i2c)
        print("[Main] VEML7700 OK")

    if 0x44 in devices:
        from sht4x import SHT4X
        sht = SHT4X(i2c)
        print("[Main] SHT4x OK")

    if 0x60 in devices:
        from mpl3115a2 import MPL3115A2
        pressure_sensor = MPL3115A2(i2c)
        print("[Main] MPL3115A2 OK")

except Exception as e:
    print("[Main] Sensor error:", e)

time.sleep(1)
display.fill_screen(display.BLACK)


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

# Main loop
print("[Main] Running...")
while True:
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

    temp_c_log = temp_c_log
    if sht:
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
        sdlog.log(date_str + " " + time_str, co2, temp_c_log, hum, lux, pressure)
    show_f = not show_f
    gc.collect()
    time.sleep(LOG_INTERVAL)
