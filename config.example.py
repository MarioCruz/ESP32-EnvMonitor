# Copy this file to config.py and fill in your WiFi credentials
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# Multiple networks - tries each in order until one connects
WIFI_NETWORKS = [
    ("YOUR_WIFI_SSID", "YOUR_WIFI_PASSWORD"),
    # ("Network2", "password2"),
    # ("Network3", "password3"),
]

# Touch screen (E32R40T model with XPT2046)
TOUCH_ENABLED = True

# I2C pins for ESP32 E32R40T board
I2C_SCL_PIN = 25
I2C_SDA_PIN = 32
I2C_FREQUENCY = 100000

# Timezone offset from UTC (e.g., US Eastern = -5)
TIMEZONE_OFFSET = -5
