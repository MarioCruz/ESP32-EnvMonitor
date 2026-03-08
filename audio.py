"""Audio module for ESP32 EnvMonitor
Uses PWM on GPIO26 with enable pin GPIO4 (low=on)
"""
import machine
import time

_pwm = None
_en = None


def _init_hw():
    global _en
    if _en is None:
        _en = machine.Pin(4, machine.Pin.OUT, value=1)


def _tone(freq, duration_ms):
    """Play a tone using PWM"""
    global _pwm
    if freq <= 0:
        time.sleep_ms(duration_ms)
        return
    _pwm = machine.PWM(machine.Pin(26), freq=freq, duty=512)
    time.sleep_ms(duration_ms)
    _pwm.deinit()
    _pwm = None


def enable():
    _init_hw()
    _en.value(0)
    time.sleep_ms(20)


def disable():
    global _pwm
    _init_hw()
    if _pwm:
        _pwm.deinit()
        _pwm = None
    _en.value(1)


# Note frequencies
_NOTES = {
    'C4': 262, 'D4': 294, 'E4': 330, 'F4': 349,
    'G4': 392, 'A4': 440, 'B4': 494,
    'C5': 523, 'D5': 587, 'E5': 659, 'F5': 698, 'G5': 784,
    'R': 0,
}


def play_notes(notes, bpm=120):
    """Play a list of (note, beats) tuples."""
    beat_ms = int(60000 / bpm)
    enable()
    for note, beats in notes:
        dur = int(beat_ms * beats * 0.85)
        gap = int(beat_ms * beats * 0.15)
        freq = _NOTES.get(note, 0)
        if freq > 0:
            _tone(freq, dur)
        time.sleep_ms(gap)
    disable()


def boot_melody():
    """Startup riff"""
    riff = [
        ('E4', 0.5),
        ('G4', 0.5),
        ('A4', 1.0),
        ('B4', 0.5),
        ('A4', 0.5),
        ('G4', 1.0),
        ('E4', 2.0),
    ]
    play_notes(riff, bpm=120)


def beep(freq=1000, ms=100):
    """Simple beep"""
    enable()
    _tone(freq, ms)
    disable()


def alert_tone():
    """CO2 alert - two quick high beeps"""
    enable()
    _tone(880, 150)
    time.sleep_ms(50)
    _tone(880, 150)
    disable()
