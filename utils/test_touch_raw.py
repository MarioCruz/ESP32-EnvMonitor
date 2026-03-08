"""
Raw touch debug - shows crosshair where you touch.
Corners labeled on screen for reference.
"""

from machine import Pin
import time
import display

T_CS  = Pin(33, Pin.OUT, value=1)
T_IRQ = Pin(36, Pin.IN)


def raw_read():
    """Read raw 12-bit XPT2046 values. Returns (cmd1_val, cmd2_val) or None."""
    if T_IRQ.value() != 0:
        return None

    display.spi.init(baudrate=2000000)
    display.cs.value(1)

    vals = []
    for cmd in [0x90, 0xD0]:
        T_CS.value(0)
        display.spi.write(bytes([cmd]))
        raw = display.spi.read(2)
        v = ((raw[0] << 8) | raw[1]) >> 3
        T_CS.value(1)
        vals.append(v)

    display.spi.init(baudrate=20000000)

    if vals[0] < 100 or vals[1] < 100:
        return None
    return (vals[0], vals[1])


def run():
    display.init()
    display.fill_screen(display.BLACK)

    # Label corners for reference
    display.draw_text("TL", 4, 4, display.GRAY, display.BLACK, 1)
    display.draw_text("TR", display.W - 36, 4, display.GRAY, display.BLACK, 1)
    display.draw_text("BL", 4, display.H - 20, display.GRAY, display.BLACK, 1)
    display.draw_text("BR", display.W - 36, display.H - 20, display.GRAY, display.BLACK, 1)

    # Center instructions
    msg = "Touch screen"
    mx = (display.W - display.text_px(msg, 2)) // 2
    display.draw_text(msg, mx, 140, display.CYAN, display.BLACK, 2)

    print("Touch the screen. Showing raw values.")
    print("0x90=?, 0xD0=?")
    print("Tap each corner and note the values.")
    print("Ctrl+C to stop.\n")

    while True:
        r = raw_read()
        if r is not None:
            v90, vD0 = r
            print("  0x90={:4d}  0xD0={:4d}".format(v90, vD0))

            # Show on screen
            display.fill_rect(60, 180, 360, 40, display.BLACK)
            line1 = "0x90={} 0xD0={}".format(v90, vD0)
            lx = (display.W - display.text_px(line1, 1)) // 2
            display.draw_text(line1, lx, 185, display.YELLOW, display.BLACK, 1)

        time.sleep_ms(150)


if __name__ == "__main__":
    run()
