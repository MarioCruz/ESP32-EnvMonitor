"""
ST7796S Display Driver + Dashboard UI for E32R40T/E32N40T
4.0" 480x320 TFT via SPI
"""
from machine import Pin, SPI
import time
from font16 import FONT16

# --- Hardware pins ---
cs = Pin(15, Pin.OUT, value=1)
dc = Pin(2, Pin.OUT, value=0)
bl = Pin(27, Pin.OUT, value=1)

spi = SPI(1, baudrate=20000000, polarity=0, phase=0,
          sck=Pin(14), mosi=Pin(13), miso=Pin(12))

W = 480
H = 320

# --- Colors (RGB565) ---
BLACK   = 0x0000
WHITE   = 0xFFFF
DKGRAY  = 0x2104
GRAY    = 0x4208
LTGRAY  = 0x8410
GREEN   = 0x07E0
RED     = 0xF800
ORANGE  = 0xFD20
CYAN    = 0x07FF
BLUE    = 0x001F
YELLOW  = 0xFFE0
DKBLUE  = 0x0010
CARD_BG  = 0x1082
CARD_BRD = 0x2945


# --- Low-level SPI commands ---

def cmd(c):
    cs.value(0)
    dc.value(0)
    spi.write(bytes([c]))
    cs.value(1)


def cmd_data(c, d):
    cs.value(0)
    dc.value(0)
    spi.write(bytes([c]))
    dc.value(1)
    spi.write(bytes(d) if isinstance(d, list) else bytes([d]))
    cs.value(1)


# --- Display init ---

def init():
    """Initialize ST7796S in landscape mode"""
    bl.value(1)
    cmd(0x01); time.sleep_ms(200)
    cmd(0x11); time.sleep_ms(200)
    cmd_data(0xF0, [0xC3])
    cmd_data(0xF0, [0x96])
    cmd_data(0x36, [0x28])  # Landscape
    cmd_data(0x3A, [0x55])  # 16-bit color
    cmd_data(0xB5, [0x02, 0x03, 0x00, 0x04])
    cmd_data(0xB6, [0x80, 0x02, 0x3B])
    cmd_data(0xB1, [0x80, 0x10])
    cmd_data(0xB4, [0x00])
    cmd_data(0xC1, [0x13])
    cmd_data(0xC2, [0xA7])
    cmd_data(0xC5, [0x09])
    cmd_data(0xE0, [0xF0,0x09,0x0B,0x06,0x04,0x15,0x2F,0x54,0x42,0x3C,0x17,0x14,0x18,0x1B])
    cmd_data(0xE1, [0xE0,0x09,0x0B,0x06,0x04,0x03,0x2B,0x43,0x42,0x3B,0x16,0x14,0x17,0x1B])
    cmd_data(0xF0, [0x3C])
    cmd_data(0xF0, [0x69])
    time.sleep_ms(200)
    cmd(0x29); time.sleep_ms(100)
    cmd(0x13)


def backlight(on=True):
    bl.value(1 if on else 0)


# --- Drawing primitives ---

def set_window(x0, y0, x1, y1):
    cmd_data(0x2A, [x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF])
    cmd_data(0x2B, [y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF])
    cmd(0x2C)


def fill_rect(x, y, w, h, color):
    x = max(0, x); y = max(0, y)
    x2 = min(W - 1, x + w - 1); y2 = min(H - 1, y + h - 1)
    rw = x2 - x + 1; rh = y2 - y + 1
    if rw <= 0 or rh <= 0:
        return
    set_window(x, y, x2, y2)
    hi = color >> 8; lo = color & 0xFF
    chunk = bytes([hi, lo] * min(rw * rh, 640))
    total = rw * rh
    cs.value(0); dc.value(1)
    while total > 0:
        n = min(total, 640)
        if n == 640:
            spi.write(chunk)
        else:
            spi.write(bytes([hi, lo] * n))
        total -= n
    cs.value(1)


def fill_screen(color):
    fill_rect(0, 0, W, H, color)


def hline(x, y, w, color):
    fill_rect(x, y, w, 1, color)


def vline(x, y, h, color):
    fill_rect(x, y, 1, h, color)


def round_rect(x, y, w, h, color, thick=2):
    fill_rect(x + 2, y, w - 4, thick, color)
    fill_rect(x + 2, y + h - thick, w - 4, thick, color)
    fill_rect(x, y + 2, thick, h - 4, color)
    fill_rect(x + w - thick, y + 2, thick, h - 4, color)


# --- Text rendering ---

def draw_char16(ch, x, y, fg, bg, scale=2):
    glyph = FONT16.get(ch, FONT16.get(' ', [0]*16))
    cw = 16 * scale; ch_ = 16 * scale
    if x + cw > W or y + ch_ > H or x < 0 or y < 0:
        return
    set_window(x, y, x + cw - 1, y + ch_ - 1)
    fghi = fg >> 8; fglo = fg & 0xFF
    bghi = bg >> 8; bglo = bg & 0xFF
    cs.value(0); dc.value(1)
    for row in range(16):
        bits = glyph[row]
        row_buf = bytearray(cw * 2)
        for col in range(16):
            if bits & (0x8000 >> col):
                hi, lo = fghi, fglo
            else:
                hi, lo = bghi, bglo
            for s in range(scale):
                idx = (col * scale + s) * 2
                row_buf[idx] = hi
                row_buf[idx + 1] = lo
        rb = bytes(row_buf)
        for _ in range(scale):
            spi.write(rb)
    cs.value(1)


def draw_text(text, x, y, fg, bg, scale=2):
    for i, ch in enumerate(text):
        draw_char16(ch, x + i * 16 * scale, y, fg, bg, scale)


def text_px(text, scale=2):
    return len(text) * 16 * scale


# --- Dashboard UI ---

def draw_card(x, y, w, h, label, value, unit, val_color, bg=CARD_BG):
    """Draw a sensor reading card"""
    fill_rect(x, y, w, h, bg)
    round_rect(x, y, w, h, CARD_BRD, 2)
    lx = x + (w - text_px(label, 1)) // 2
    draw_text(label, lx, y + 6, LTGRAY, bg, 1)
    vx = x + (w - text_px(value, 2)) // 2
    draw_text(value, vx, y + 30, val_color, bg, 2)
    ux = x + (w - text_px(unit, 1)) // 2
    draw_text(unit, ux, y + 68, GRAY, bg, 1)


def draw_dashboard(co2, temp, hum, status="Normal"):
    """Draw the full EnvMonitor dashboard - 2x2 grid"""
    # Title bar
    fill_rect(0, 0, W, 28, DKBLUE)
    draw_text("EnvMonitor", 8, 6, CYAN, DKBLUE, 1)
    fill_rect(W - 40, 8, 10, 10, GREEN)
    draw_text("ON", W - 28, 6, GREEN, DKBLUE, 1)

    # Card layout
    card_w = 230
    card_h = 88
    gap = 8
    row1_y = 34
    row2_y = row1_y + card_h + gap
    x0 = (W - (2 * card_w + gap)) // 2

    # CO2
    co2_color = GREEN if co2 < 1000 else (YELLOW if co2 < 1500 else RED)
    draw_card(x0, row1_y, card_w, card_h, "CO2", str(co2), "ppm", co2_color)

    # Temperature
    draw_card(x0 + card_w + gap, row1_y, card_w, card_h,
              "TEMP", "{:.1f}".format(temp), "F", ORANGE)

    # Humidity
    draw_card(x0, row2_y, card_w, card_h,
              "HUMIDITY", "{:.1f}".format(hum), "%", CYAN)

    # Status / WiFi card
    sx = x0 + card_w + gap
    fill_rect(sx, row2_y, card_w, card_h, CARD_BG)
    round_rect(sx, row2_y, card_w, card_h, CARD_BRD, 2)
    draw_text("WIFI", sx + (card_w - text_px("WIFI", 1)) // 2, row2_y + 6, LTGRAY, CARD_BG, 1)
    # Use scale 1 for IP addresses (they're long), scale 2 for short status
    if len(status) > 10:
        vx = sx + (card_w - text_px(status, 1)) // 2
        s_color = GREEN if "." in status else RED
        draw_text(status, vx, row2_y + 38, s_color, CARD_BG, 1)
    else:
        vx = sx + (card_w - text_px(status, 2)) // 2
        s_color = GREEN if status != "No WiFi" else RED
        draw_text(status, vx, row2_y + 30, s_color, CARD_BG, 2)
    draw_text("ESP32", sx + (card_w - text_px("ESP32", 1)) // 2, row2_y + 68, GRAY, CARD_BG, 1)

    # Bottom bar
    fill_rect(0, H - 18, W, 18, DKBLUE)
    draw_text("ESP32 EnvMonitor", 8, H - 16, GRAY, DKBLUE, 1)
