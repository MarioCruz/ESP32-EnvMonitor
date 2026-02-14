"""SD Card CSV Logger for EnvMonitor"""
import machine
import os

_sd = None
_mounted = False
_LOG_FILE = "/sd/envlog.csv"


def init():
    """Mount SD card. Returns True if successful."""
    global _sd, _mounted
    try:
        import sdcard
        spi2 = machine.SPI(2, baudrate=1000000,
                           sck=machine.Pin(18),
                           mosi=machine.Pin(23),
                           miso=machine.Pin(19))
        cs = machine.Pin(5, machine.Pin.OUT)
        _sd = sdcard.SDCard(spi2, cs)
        os.mount(_sd, "/sd")
        _mounted = True
        # Write header if file doesn't exist
        try:
            os.stat(_LOG_FILE)
        except:
            with open(_LOG_FILE, "w") as f:
                f.write("timestamp,co2,temp_c,humidity,lux,pressure_hpa\n")
        print("[SD] Mounted OK")
        return True
    except Exception as e:
        print("[SD] Error:", e)
        _mounted = False
        return False


def log(timestamp, co2, temp_c, humidity, lux, pressure):
    """Append one row to CSV"""
    if not _mounted:
        return False
    try:
        with open(_LOG_FILE, "a") as f:
            f.write("{},{},{:.1f},{:.1f},{},{:.0f}\n".format(
                timestamp, co2, temp_c, humidity, int(lux), pressure))
        return True
    except Exception as e:
        print("[SD] Write error:", e)
        return False


def is_mounted():
    return _mounted


def free_space():
    """Return SD usage as percentage string"""
    if not _mounted:
        return "--"
    try:
        stat = os.statvfs("/sd")
        total = stat[0] * stat[2]
        free = stat[0] * stat[3]
        used_pct = int(100 * (total - free) / total) if total > 0 else 0
        return "{}%".format(used_pct)
    except:
        return "?"
