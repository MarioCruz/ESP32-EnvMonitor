"""WiFi connection manager for ESP32"""
import network
import time

wlan = network.WLAN(network.STA_IF)


def connect(ssid, password, timeout=20):
    """Connect to WiFi. Returns (ip_address, True) or (error_msg, False)"""
    wlan.active(True)

    if wlan.isconnected():
        return wlan.ifconfig()[0], True

    print("Connecting to WiFi:", ssid)
    wlan.connect(ssid, password)

    start = time.time()
    while not wlan.isconnected():
        if time.time() - start > timeout:
            print("WiFi timeout, status:", wlan.status())
            wlan.disconnect()
            return "Timeout", False
        time.sleep(0.5)

    ip = wlan.ifconfig()[0]
    print("Connected:", ip)
    return ip, True


def connect_multi(networks, timeout=15):
    """Try multiple networks in order. Returns (ip, True) or (error, False)"""
    wlan.active(True)
    if wlan.isconnected():
        return wlan.ifconfig()[0], True
    for ssid, pw in networks:
        print("Trying WiFi:", ssid)
        ip, ok = connect(ssid, pw, timeout)
        if ok:
            return ip, True
    return "No network", False


def is_connected():
    return wlan.active() and wlan.isconnected()


def get_ip():
    if wlan.isconnected():
        return wlan.ifconfig()[0]
    return None


def disconnect():
    wlan.disconnect()
    wlan.active(False)
