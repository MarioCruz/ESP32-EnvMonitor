"""
XPT2046 Resistive Touch Driver for E32R40T
============================================
Shares SPI bus with ST7796S display.
Pins: Touch CS=GPIO33, Touch IRQ=GPIO36
"""

from machine import Pin
import display

T_CS  = Pin(33, Pin.OUT, value=1)
T_IRQ = Pin(36, Pin.IN)

# Calibration for 480x320 landscape
# 0x90 = X axis: 3850 (left) to 270 (right)
# 0xD0 = Y axis: 3720 (top) to 380 (bottom)
X_MIN = 270
X_MAX = 3850
Y_MIN = 380
Y_MAX = 3720


def read():
    """Read touch position. Returns (x, y) in screen coords or None."""
    if T_IRQ.value() != 0:
        return None

    # Slow SPI for XPT2046 (max ~2MHz)
    display.spi.init(baudrate=2000000)
    display.cs.value(1)

    samples_x = []
    samples_y = []

    for _ in range(5):
        T_CS.value(0)
        display.spi.write(bytes([0x90]))  # X channel
        raw = display.spi.read(2)
        rx = ((raw[0] << 8) | raw[1]) >> 3
        T_CS.value(1)

        T_CS.value(0)
        display.spi.write(bytes([0xD0]))  # Y channel
        raw = display.spi.read(2)
        ry = ((raw[0] << 8) | raw[1]) >> 3
        T_CS.value(1)

        if 100 < rx < 4000 and 100 < ry < 4000:
            samples_x.append(rx)
            samples_y.append(ry)

    # Restore fast SPI for display
    display.spi.init(baudrate=20000000)

    if len(samples_x) < 2:
        return None

    samples_x.sort()
    samples_y.sort()
    mid = len(samples_x) // 2
    rx = samples_x[mid]
    ry = samples_y[mid]

    # Both axes inverted: high raw = low screen coord
    x = display.W - 1 - (rx - X_MIN) * display.W // (X_MAX - X_MIN)
    y = display.H - 1 - (ry - Y_MIN) * display.H // (Y_MAX - Y_MIN)
    x = max(0, min(display.W - 1, x))
    y = max(0, min(display.H - 1, y))

    return (x, y)
