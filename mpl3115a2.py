"""MPL3115A2 Barometric Pressure / Altitude / Temperature Sensor Driver
From Growing-Beyond-Earth/gbe-micropython, cleaned up for ESP32 EnvMonitor
I2C address: 0x60
"""
import time

MPL3115_I2CADDR = const(0x60)
MPL3115_STATUS = const(0x00)
MPL3115_PRESSURE_DATA_MSB = const(0x01)
MPL3115_TEMP_DATA_MSB = const(0x04)
MPL3115_TEMP_DATA_LSB = const(0x05)
MPL3115_PT_DATA_CFG = const(0x13)
MPL3115_CTRL_REG1 = const(0x26)

PRESSURE = const(0)
ALTITUDE = const(1)


class MPL3115A2:
    def __init__(self, i2c, mode=PRESSURE):
        self.i2c = i2c
        self.addr = MPL3115_I2CADDR
        self.mode = mode
        self._buf = bytearray(1)
        self._last_p = 0.0

        if mode == PRESSURE:
            # Barometer mode, oversampling 128, min time 512ms
            self.i2c.writeto_mem(self.addr, MPL3115_CTRL_REG1, bytes([0x38]))
            self.i2c.writeto_mem(self.addr, MPL3115_PT_DATA_CFG, bytes([0x07]))
            self.i2c.writeto_mem(self.addr, MPL3115_CTRL_REG1, bytes([0x39]))
        elif mode == ALTITUDE:
            # Altitude mode, oversampling 128
            self.i2c.writeto_mem(self.addr, MPL3115_CTRL_REG1, bytes([0xB8]))
            self.i2c.writeto_mem(self.addr, MPL3115_PT_DATA_CFG, bytes([0x07]))
            self.i2c.writeto_mem(self.addr, MPL3115_CTRL_REG1, bytes([0xB9]))
        else:
            raise ValueError("Invalid mode")

        # Wait for first reading
        if not self._wait_ready(timeout=2000):
            raise OSError("MPL3115A2 not responding")

    def _wait_ready(self, timeout=600):
        start = time.ticks_ms()
        while True:
            self.i2c.readfrom_mem_into(self.addr, MPL3115_STATUS, self._buf)
            if self._buf[0] & 0x04:
                return True
            if time.ticks_diff(time.ticks_ms(), start) > timeout:
                return False
            time.sleep_ms(10)

    def pressure(self):
        """Read pressure in Pascals, returns hPa (mbar)"""
        if self.mode != PRESSURE:
            raise ValueError("Not in pressure mode")
        if not self._wait_ready():
            return self._last_p
        data = self.i2c.readfrom_mem(self.addr, MPL3115_PRESSURE_DATA_MSB, 3)
        p_int = (data[0] << 10) | (data[1] << 2) | ((data[2] >> 6) & 0x03)
        p_frac = (data[2] >> 4) & 0x03
        self._last_p = (p_int + p_frac / 4.0) / 100.0
        return self._last_p

    def altitude(self):
        """Read altitude in meters"""
        if self.mode != ALTITUDE:
            raise ValueError("Not in altitude mode")
        self._wait_ready()
        data = self.i2c.readfrom_mem(self.addr, MPL3115_PRESSURE_DATA_MSB, 3)
        alt_int = (data[0] << 8) | data[1]
        alt_frac = (data[2] >> 4) & 0x0F
        if alt_int > 32767:
            alt_int -= 65536
        return alt_int + alt_frac / 16.0

    def temperature(self):
        """Read temperature in Celsius"""
        self._wait_ready()
        msb = self.i2c.readfrom_mem(self.addr, MPL3115_TEMP_DATA_MSB, 1)
        lsb = self.i2c.readfrom_mem(self.addr, MPL3115_TEMP_DATA_LSB, 1)
        t = msb[0]
        if t > 127:
            t -= 256
        return t + lsb[0] / 256.0
