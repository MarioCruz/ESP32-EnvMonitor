"""Simple SHT4x temperature/humidity sensor driver"""
import time
import struct

SHT4X_ADDR = 0x44
_MEASURE_HIGH = 0xFD  # High precision measurement


def _crc8(data):
    crc = 0xFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x31
            else:
                crc = crc << 1
            crc &= 0xFF
    return crc


class SHT4X:
    def __init__(self, i2c, address=SHT4X_ADDR):
        self.i2c = i2c
        self.addr = address
        self._temp = 0.0
        self._hum = 0.0

    def read(self):
        """Take a measurement. Returns (temp_c, humidity)"""
        self.i2c.writeto(self.addr, bytes([_MEASURE_HIGH]))
        time.sleep_ms(10)
        data = self.i2c.readfrom(self.addr, 6)
        # Check CRCs
        if _crc8(data[0:2]) != data[2] or _crc8(data[3:5]) != data[5]:
            raise ValueError("SHT4x CRC error")
        t_raw = (data[0] << 8) | data[1]
        h_raw = (data[3] << 8) | data[4]
        self._temp = -45.0 + 175.0 * t_raw / 65535.0
        self._hum = max(0.0, min(100.0, -6.0 + 125.0 * h_raw / 65535.0))
        return self._temp, self._hum

    @property
    def temperature(self):
        return self._temp

    @property
    def humidity(self):
        return self._hum
