import time
import random
import display

# Initialize the display
display.init()
display.fill_screen(display.BLACK)

# Draw initial dashboard with mock data
display.draw_dashboard(co2=823, temp=74.5, hum=45.2)

# TODO: Replace with real SCD4x sensor reads
# from machine import I2C, Pin
# i2c = I2C(0, scl=Pin(25), sda=Pin(32))
# import scd4x
# sensor = scd4x.SCD4X(i2c)
# sensor.start_periodic_measurement()

while True:
    time.sleep(3)

    # Mock data - replace with sensor.read() later
    co2 = random.randint(400, 1800)
    temp = 70.0 + random.uniform(-5, 10)
    hum = 40.0 + random.uniform(-10, 20)

    display.draw_dashboard(co2, temp, hum)
