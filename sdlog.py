"""SD Card CSV Logger for EnvMonitor"""
import machine
import os

_sd = None
_mounted = False
_LOG_FILE = "/sd/envlog.csv"
_LOG_DIR = "/sd"


def init():
    """Mount SD card. Returns True if successful."""
    global _sd, _mounted
    try:
        # Always unmount first if previously mounted
        try:
            os.umount("/sd")
        except:
            pass
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


def _log_filename(t):
    """Get log filename for given localtime tuple: envlog_YYMMDD.csv"""
    return "{}/envlog_{:02d}{:02d}{:02d}.csv".format(
        _LOG_DIR, t[0] % 100, t[1], t[2])


def log(timestamp, co2, temp_c, humidity, lux, pressure, localtime=None):
    """Append one row to CSV, rotating file daily"""
    if not _mounted:
        return False
    try:
        fname = _log_filename(localtime) if localtime else _LOG_FILE
        # Write header if new file
        try:
            os.stat(fname)
        except:
            with open(fname, "w") as f:
                f.write("timestamp,co2,temp_c,humidity,lux,pressure_hpa\n")
        with open(fname, "a") as f:
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
