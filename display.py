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
CARD_BG  = 0x2945
CARD_BRD = 0x4A69


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


def show_logo(filename="logo.bin"):
    """Display RGB565 logo from binary file, centered on screen with line-by-line reveal"""
    import struct
    try:
        f = open(filename, 'rb')
        hdr = f.read(4)
        iw, ih = struct.unpack('>HH', hdr)
        x0 = (W - iw) // 2
        y0 = (H - ih) // 2
        fill_screen(WHITE)
        # Reveal line by line for a cool wipe effect
        row_bytes = iw * 2
        for row in range(ih):
            set_window(x0, y0 + row, x0 + iw - 1, y0 + row)
            data = f.read(row_bytes)
            if not data:
                break
            cs.value(0)
            dc.value(1)
            spi.write(data)
            cs.value(1)
        f.close()
        return True
    except Exception as e:
        print("[Display] Logo error:", e)
        return False


def _rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def boot_progress(pct, msg="", msg_color=CYAN):
    """Draw animated boot progress bar at bottom of screen"""
    bar_y = H - 48
    bar_h = 22
    bar_x = 40
    bar_w = W - 80
    # Background bar
    fill_rect(bar_x, bar_y, bar_w, bar_h, DKGRAY)
    # Gradient fill - cyan to green
    filled = int(bar_w * pct / 100)
    if filled > 0:
        step = max(1, filled // 20)
        for i in range(0, filled, step):
            blend = i * 255 // bar_w
            r = 0
            g = 128 + (blend >> 1)
            b = 255 - blend
            c = _rgb565(r, g, b)
            sw = min(step, filled - i)
            fill_rect(bar_x + i, bar_y, sw, bar_h, c)
    # Bright tip
    if filled > 2:
        fill_rect(bar_x + filled - 2, bar_y, 2, bar_h, WHITE)
    # Status text below bar
    fill_rect(0, bar_y + bar_h + 2, W, 20, BLACK)
    if msg:
        mx = (W - text_px(msg, 1)) // 2
        draw_text(msg, mx, bar_y + bar_h + 4, msg_color, BLACK, 1)


def boot_title():
    """Draw the boot title with scanning line effect"""
    fill_screen(BLACK)
    # Horizontal scan lines sweep
    for i in range(0, H, 4):
        c = _rgb565(0, int(i * 0.4), int(i * 0.8) & 0xFF)
        hline(0, i, W, c)
        if i % 16 == 0:
            time.sleep_ms(5)
    time.sleep_ms(200)
    fill_screen(BLACK)
    # Title
    title = "EnvMonitor"
    tx = (W - text_px(title, 3)) // 2
    # Draw each letter with a slight delay
    for i, ch in enumerate(title):
        draw_char16(ch, tx + i * 48, 100, CYAN, BLACK, 3)
        time.sleep_ms(60)
    # Subtitle
    time.sleep_ms(300)
    sub = "Environmental Monitor"
    sx = (W - text_px(sub, 1)) // 2
    draw_text(sub, sx, 160, LTGRAY, BLACK, 1)
    # Version line
    ver = "v1.0"
    vx = (W - text_px(ver, 1)) // 2
    draw_text(ver, vx, 185, GRAY, BLACK, 1)


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
    draw_text(label, lx, y + 4, WHITE, bg, 1)
    # Clamp value to fit card width
    vscale = 2
    if text_px(value, 2) > w - 8:
        vscale = 1
    vx = x + (w - text_px(value, vscale)) // 2
    draw_text(value, vx, y + 24, val_color, bg, vscale)
    ux = x + (w - text_px(unit, 1)) // 2
    draw_text(unit, ux, y + 60, LTGRAY, bg, 1)


def draw_dashboard(co2, temp, hum, lux=0, pressure=0, sd_free="--",
                   status="", unit_label="F", time_str="", date_str=""):
    """Draw the full EnvMonitor dashboard - 3x3 grid"""
    # Title bar
    fill_rect(0, 0, W, 26, DKBLUE)
    draw_text("EnvMonitor", 8, 5, CYAN, DKBLUE, 1)
    fill_rect(W - 14, 8, 10, 10, GREEN)

    # 3x3 card grid
    card_w = 152
    card_h = 78
    gap = 5
    row1_y = 28
    row2_y = row1_y + card_h + gap
    row3_y = row2_y + card_h + gap
    x0 = (W - (3 * card_w + 2 * gap)) // 2

    # Row 1: CO2, Temperature, Humidity
    co2_color = GREEN if co2 < 1000 else (YELLOW if co2 < 1500 else RED)
    draw_card(x0, row1_y, card_w, card_h, "CO2", str(co2), "ppm", co2_color)

    draw_card(x0 + card_w + gap, row1_y, card_w, card_h,
              "TEMP", "{:.1f}".format(temp), unit_label, ORANGE)

    draw_card(x0 + 2 * (card_w + gap), row1_y, card_w, card_h,
              "HUMID", "{:.1f}".format(hum), "%", CYAN)

    # Row 2: Light, Air Quality, Pressure
    lux_str = str(int(lux))
    lux_color = YELLOW if lux < 10 else (GREEN if lux < 1000 else WHITE)
    draw_card(x0, row2_y, card_w, card_h, "LIGHT", lux_str, "lux", lux_color)

    co2_status = "Good" if co2 < 1000 else ("Fair" if co2 < 1500 else "Poor")
    co2_st_color = GREEN if co2 < 1000 else (YELLOW if co2 < 1500 else RED)
    draw_card(x0 + card_w + gap, row2_y, card_w, card_h,
              "AIR", co2_status, "quality", co2_st_color)

    p_str = "{:.0f}".format(pressure) if pressure > 0 else "--"
    draw_card(x0 + 2 * (card_w + gap), row2_y, card_w, card_h,
              "PRESS", p_str, "hPa", WHITE)

    # Row 3: SD Card, WiFi, Time
    draw_card(x0, row3_y, card_w, card_h, "SD", sd_free, "used", GREEN)

    wifi_str = "OK" if "." in status else "OFF"
    wifi_color = GREEN if "." in status else RED
    draw_card(x0 + card_w + gap, row3_y, card_w, card_h,
              "WIFI", wifi_str, "", wifi_color)

    # Time card - draw manually with scale 1 value
    tx3 = x0 + 2 * (card_w + gap)
    fill_rect(tx3, row3_y, card_w, card_h, CARD_BG)
    round_rect(tx3, row3_y, card_w, card_h, CARD_BRD, 2)
    tlx = tx3 + (card_w - text_px("TIME", 1)) // 2
    draw_text("TIME", tlx, row3_y + 4, WHITE, CARD_BG, 1)
    if time_str:
        tvx = tx3 + (card_w - text_px(time_str, 1)) // 2
        draw_text(time_str, tvx, row3_y + 28, YELLOW, CARD_BG, 1)
    if date_str:
        dvx = tx3 + (card_w - text_px(date_str, 1)) // 2
        draw_text(date_str, dvx, row3_y + 48, LTGRAY, CARD_BG, 1)

    # Bottom bar with IP
    bot_y = row3_y + card_h + 2
    fill_rect(0, bot_y, W, H - bot_y, DKBLUE)
    if status and "." in status:
        ip_x = (W - text_px(status, 1)) // 2
        draw_text(status, ip_x, bot_y + 1, GREEN, DKBLUE, 1)
