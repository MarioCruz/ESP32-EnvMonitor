"""WiFi connection manager for ESP32"""
import network
import time


def connect(ssid, password, timeout=15):
    """Connect to WiFi. Returns (ip_address, True) or (error_msg, False)"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        return wlan.ifconfig()[0], True

    print("Connecting to WiFi:", ssid)
    wlan.connect(ssid, password)

    start = time.time()
    while not wlan.isconnected():
        if time.time() - start > timeout:
            wlan.active(False)
            return "Timeout", False
        time.sleep(0.5)

    ip = wlan.ifconfig()[0]
    print("Connected:", ip)
    return ip, True


def is_connected():
    wlan = network.WLAN(network.STA_IF)
    return wlan.isconnected()


def get_ip():
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        return wlan.ifconfig()[0]
    return None


def disconnect():
    wlan = network.WLAN(network.STA_IF)
    wlan.disconnect()
    wlan.active(False)
