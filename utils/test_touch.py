"""
XPT2046 Resistive Touch Test for E32R40T
==========================================
Tap 4 boxes on the touchscreen to confirm touch works.
Uses touch.py driver (Touch CS=GPIO33, Touch IRQ=GPIO36)
"""

import time
import display
import touch


# --- Visual Test ---

BOX_W = 200
BOX_H = 60

BOXES = [
    {'label': 'TOP LEFT',     'x': 10,              'y': 10},
    {'label': 'TOP RIGHT',    'x': display.W - 210,  'y': 10},
    {'label': 'BTM LEFT',     'x': 10,              'y': display.H - 70},
    {'label': 'BTM RIGHT',    'x': display.W - 210,  'y': display.H - 70},
]


def _hit_test(tx, ty, box):
    return (box['x'] <= tx <= box['x'] + BOX_W and
            box['y'] <= ty <= box['y'] + BOX_H)


def _draw_box(box, state='idle'):
    x, y = box['x'], box['y']
    if state == 'confirmed':
        bg, border, fg, status = display.GREEN, display.WHITE, display.BLACK, "OK!"
    elif state == 'touched':
        bg, border, fg, status = display.CYAN, display.WHITE, display.BLACK, "TOUCHED!"
    else:
        bg, border, fg, status = display.CARD_BG, display.CARD_BRD, display.WHITE, "Tap here"

    display.fill_rect(x, y, BOX_W, BOX_H, bg)
    display.round_rect(x, y, BOX_W, BOX_H, border, 2)
    lx = x + (BOX_W - display.text_px(box['label'], 1)) // 2
    display.draw_text(box['label'], lx, y + 8, fg, bg, 1)
    sx = x + (BOX_W - display.text_px(status, 1)) // 2
    display.draw_text(status, sx, y + 34, fg, bg, 1)


def run():
    """Run the visual touch box test."""
    print("Initializing display...")
    display.init()
    print("Drawing UI...")
    display.fill_screen(display.BLACK)

    # Title
    title = "Touch Test"
    tx = (display.W - display.text_px(title, 2)) // 2
    display.draw_text(title, tx, display.H // 2 - 16, display.CYAN, display.BLACK, 2)

    # Footer
    foot = "Tap each box"
    fx = (display.W - display.text_px(foot, 1)) // 2
    display.draw_text(foot, fx, display.H // 2 + 20, display.LTGRAY, display.BLACK, 1)

    # Draw boxes
    confirmed = [False] * len(BOXES)
    for i, box in enumerate(BOXES):
        _draw_box(box, 'idle')

    print("UI drawn. Waiting for touch... (Ctrl+C to stop)")

    # Raw readout area
    raw_y = display.H // 2 + 44
    prev_touch = False

    while not all(confirmed):
        try:
            pos = touch.read()
        except Exception as e:
            print("Touch error:", e)
            time.sleep_ms(500)
            continue

        if pos is not None:
            px, py = pos
            # Show coordinates
            display.fill_rect(100, raw_y, 280, 18, display.BLACK)
            coord_str = "x={} y={}".format(px, py)
            cx = (display.W - display.text_px(coord_str, 1)) // 2
            display.draw_text(coord_str, cx, raw_y, display.YELLOW, display.BLACK, 1)
            print("  screen: x={} y={}".format(px, py))

            if not prev_touch:
                for i, box in enumerate(BOXES):
                    if not confirmed[i] and _hit_test(px, py, box):
                        confirmed[i] = True
                        _draw_box(box, 'confirmed')
                        print("  {} confirmed!".format(box['label']))
            prev_touch = True
        else:
            prev_touch = False

        time.sleep_ms(50)

    # All done
    display.fill_rect(0, raw_y, display.W, 20, display.BLACK)
    msg = "All confirmed!"
    mx = (display.W - display.text_px(msg, 2)) // 2
    display.draw_text(msg, mx, display.H // 2 + 16, display.GREEN, display.BLACK, 2)
    print("All touch zones confirmed!")


if __name__ == "__main__":
    run()
