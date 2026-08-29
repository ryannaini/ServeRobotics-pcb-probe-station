"""
Serial Monitor replica for linear_actuators.ino — owns its own Arduino port.

Type exactly what you would in the Arduino Serial Monitor:
  3 or 4  ->  1 or 2  ->  f / b / t  ->  s (while moving)  ->  o (exit)

Chars are sent one byte at a time, no newline.
"""

import threading
import time

import serial
import serial.tools.list_ports

ACTUATOR_ARDUINO = "16C153BB515453484D202020FF0B2515"

ser = None
# Reentrant: the command helpers below take this lock and then call
# _send_char, which takes it again. A plain Lock deadlocks there.
_lock = threading.RLock()
_reader_stop = False

# Mirrors the Arduino session so top/bottom and speed are only re-sent on change
_current_actuator = None
_current_speed = None
_moving = False


def find_arduino_by_serial(target_serial):
    for port in serial.tools.list_ports.comports():
        if port.serial_number == target_serial:
            return port.device
    return None


def list_ports():
    print("Available ports:")
    for port in serial.tools.list_ports.comports():
        print(f"  {port.device}  serial={port.serial_number}  {port.description}")


def start_serial_program():
    global ser, _current_actuator, _current_speed, _moving
    if ser and ser.is_open:
        print(f"Already connected on {ser.port}")
        return {"status": "ok", "message": f"Already connected on {ser.port}"}

    port = find_arduino_by_serial(ACTUATOR_ARDUINO)
    if not port:
        print(f"Arduino not found (serial {ACTUATOR_ARDUINO})")
        list_ports()
        return {"status": "error", "message": f"Actuator Arduino not found ({ACTUATOR_ARDUINO})"}

    try:
        ser = serial.Serial(port, 9600, timeout=1)
    except serial.SerialException as e:
        print(f"Could not open {port}: {e}")
        print("Another program still has this port — check for:")
        print("  - another linear_actuators.py terminal waiting at input")
        print("  - python.exe in Task Manager")
        print("  - Arduino Serial Monitor")
        print("Run:  taskkill /F /IM python.exe")
        return {"status": "error", "message": f"Could not open {port}: {e}"}

    # Opening the port resets the board — wait for setup() before sending
    time.sleep(2.0)
    ser.reset_input_buffer()

    # The reset also dropped whatever session we thought we had
    _current_actuator = None
    _current_speed = None
    _moving = False

    print(f"Connected on {port}")
    return {"status": "ok", "message": f"Connected on {port}"}


def stop_serial_program():
    global ser, _reader_stop, _current_actuator, _current_speed, _moving
    _reader_stop = True
    if ser and ser.is_open:
        ser.close()
        print("Serial closed")
    ser = None
    _current_actuator = None
    _current_speed = None
    _moving = False


def _connected():
    return bool(ser and ser.is_open)


def _send_char(ch: str):
    if not _connected() or len(ch) != 1:
        return False
    with _lock:
        ser.write(ch.encode("ascii"))
        ser.flush()
    return True


def _read_loop():
    """Print everything the Arduino sends — same as Serial Monitor."""
    global _reader_stop
    while not _reader_stop and _connected():
        try:
            raw = ser.readline()
            if raw:
                print(raw.decode("utf-8", errors="replace"), end="", flush=True)
        except Exception:
            break
        time.sleep(0.01)


def start_serial_reader():
    """Echo Arduino output (ACTUATOR_READY, PROMPT_DIR, ...) to the console."""
    global _reader_stop
    if not _connected():
        return
    _reader_stop = False
    threading.Thread(target=_read_loop, daemon=True).start()


## ----------------------------------------------------------------
##          W E B S I T E   A P I

def _err(msg="Not connected to the Arduino, linear actuator"):
    return {"status": "error", "message": msg}


# The sketch's top-level loop() answers only to '3' and '4' — every other byte
# is discarded in silence. So if the board resets (opening the port does that)
# while Python still thinks a session is open, f/b/s/t vanish and the actuator
# looks dead. Confirming each step against the markers the sketch prints lets
# us notice that and rebuild the session.
ACK_TIMEOUT_S = 2.0


def _read_until(markers, timeout=ACK_TIMEOUT_S):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        raw = ser.readline()
        if not raw:
            continue
        line = raw.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        if line.startswith(tuple(markers)):
            return line
        print(f"[actuator] {line}")
    return None


def _stop_unlocked():
    global _moving
    if _moving:
        _send_char("s")
        _read_until(("ACTUATOR_STOPPED",), 1.0)
        _moving = False


def _open_session(actuator: int, speed: int):
    """Drive the board to PROMPT_DIR for this actuator and speed, from any state."""
    global _current_actuator, _current_speed

    _current_actuator = None
    _current_speed = None
    _stop_unlocked()

    # 'o' leaves an open session; at the top level it is simply ignored.
    _send_char("o")
    _read_until(("ACTUATOR_EXIT",), 0.3)
    ser.reset_input_buffer()

    _send_char(str(actuator))
    if not _read_until(("ACTUATOR_READY",)):
        return False
    if not _read_until(("PROMPT_SCALE",)):
        return False

    _send_char(str(speed))
    if not _read_until(("PROMPT_DIR",)):
        return False

    _current_actuator = actuator
    _current_speed = speed
    return True


def _ensure_session(actuator: int, speed: int):
    global _current_speed

    if _current_actuator != actuator:
        return _open_session(actuator, speed)

    if _current_speed != speed:
        # 1/2 at PROMPT_DIR changes speed without leaving the session
        _send_char(str(speed))
        if not _read_until(("SCALE_SET",)):
            return _open_session(actuator, speed)
        _current_speed = speed

    return True


def _command(ch: str, markers, actuator: int, speed: int):
    """Send one char at PROMPT_DIR; rebuild the session and retry if ignored."""
    _send_char(ch)
    ack = _read_until(markers)
    if ack:
        return ack

    if not _open_session(actuator, speed):
        return None
    _send_char(ch)
    return _read_until(markers)


def start_move(actuator: int, speed: int, direction: str):
    """Hold-to-move START — the Arduino steps until stop_move() sends 's'."""
    global _moving

    if not _connected():
        return _err()
    if actuator not in (3, 4) or speed not in (1, 2):
        return _err("actuator must be 3 or 4, speed must be 1 or 2")

    d = direction.strip().lower()
    if d in ("forward", "f"):
        action = "f"
    elif d in ("backward", "b"):
        action = "b"
    else:
        return _err("direction must be forward or backward")

    with _lock:
        if not _ensure_session(actuator, speed):
            return _err(f"Actuator {actuator} did not respond — is the board powered?")

        ack = _command(action, ("MOVING_FWD", "MOVING_BWD"), actuator, speed)
        if not ack:
            return _err(f"Actuator {actuator} ignored '{action}'")
        _moving = True

    return {
        "status": "ok",
        "message": "Moving forward" if action == "f" else "Moving backward",
        "actuator": actuator,
        "speed": speed,
    }


def stop_move():
    """Hold-to-move STOP — 's' halts motion and releases the driver enable."""
    with _lock:
        _stop_unlocked()
    return {"status": "ok", "message": "Actuator stopped"}


def step_once(actuator: int, speed: int, direction: str = "forward"):
    """Single step ('t'); the firmware only steps forward."""
    if not _connected():
        return _err()
    if actuator not in (3, 4) or speed not in (1, 2):
        return _err("actuator must be 3 or 4, speed must be 1 or 2")

    with _lock:
        if not _ensure_session(actuator, speed):
            return _err(f"Actuator {actuator} did not respond — is the board powered?")
        if not _command("t", ("STEP_ONCE",), actuator, speed):
            return _err(f"Actuator {actuator} ignored the step")

    return {"status": "ok", "message": "Stepped once", "actuator": actuator, "speed": speed}


def exit_actuator():
    """Leave the actuator menu ('o') and forget the session."""
    global _current_actuator, _current_speed
    with _lock:
        _stop_unlocked()
        if _current_actuator is not None:
            _send_char("o")
            _read_until(("ACTUATOR_EXIT",), 0.5)
        _current_actuator = None
        _current_speed = None
    return {"status": "ok", "message": "Exited actuator"}


def main():
    global _reader_stop

    start_serial_program()
    if not _connected():
        print("Not connected")
        return

    _reader_stop = False
    reader = threading.Thread(target=_read_loop, daemon=True)
    reader.start()

    print("Serial Monitor mode (9600)")
    print("  3/4 select  |  1/2 speed  |  f b t move  |  s stop  |  o exit")
    print("  Quit: q + Enter")
    print()

    try:
        while True:
            line = input()
            if not line:
                continue

            cmd = line.strip().lower()
            if cmd in ("q", "quit", "exit"):
                break

            if len(cmd) == 1 and cmd in "3412fbtso":
                _send_char(cmd)
            else:
                print("Use 3, 4, 1, 2, f, b, t, s, or o")

    finally:
        _reader_stop = True
        reader.join(timeout=1.0)
        stop_serial_program()


if __name__ == "__main__":
    main()
