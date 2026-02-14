import time
import random
import display
import wifi
from config import WIFI_SSID, WIFI_PASSWORD

# Initialize display
display.init()
display.fill_screen(display.BLACK)

# Show connecting status
display.draw_text("Connecting", 100, 140, display.CYAN, display.BLACK, 2)
display.draw_text("to WiFi...", 100, 176, display.CYAN, display.BLACK, 2)

# Connect to WiFi
ip, ok = wifi.connect(WIFI_SSID, WIFI_PASSWORD)

display.fill_screen(display.BLACK)

if ok:
    status = ip
    status_color = display.GREEN
else:
    status = "No WiFi"
    status_color = display.RED

# Draw initial dashboard
display.draw_dashboard(co2=0, temp=0.0, hum=0.0, status=status)

# TODO: Replace with real SCD4x sensor reads
# from machine import I2C, Pin
# i2c = I2C(0, scl=Pin(25), sda=Pin(32))
# import scd4x
# sensor = scd4x.SCD4X(i2c)
# sensor.start_periodic_measurement()

while True:
    time.sleep(3)

    # Check WiFi status
    if wifi.is_connected():
        status = wifi.get_ip()
    else:
        status = "No WiFi"
        # Try reconnecting
        ip, ok = wifi.connect(WIFI_SSID, WIFI_PASSWORD, timeout=5)
        if ok:
            status = ip

    # Mock data - replace with sensor.read() later
    co2 = random.randint(400, 1800)
    temp = 70.0 + random.uniform(-5, 10)
    hum = 40.0 + random.uniform(-10, 20)

    display.draw_dashboard(co2, temp, hum, status=status)
