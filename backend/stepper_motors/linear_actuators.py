"""
Linear actuators — same bytes as Arduino Serial Monitor.

IMPORTANT: sending 3/4 enters runActuator() which BLOCKS the main loop.
Flip commands only work at PROMPT_TOP. Always send o after s/t to exit actuator.
"""

import threading
import time

from stepper_motors import motors_serial

_reader_stop = False
_in_actuator = False
_moving = False
_current_actuator = None
_actuator_lock = threading.Lock()


def _connected():
    return bool(motors_serial.ser and motors_serial.ser.is_open)


def _err(msg="Not connected to the Arduino, linear actuator"):
    return {"status": "error", "message": msg}


def _ensure_serial():
    if not _connected():
        motors_serial.start_serial_program()
    return _connected()


def _send_char(ch: str):
    return motors_serial.write_char(ch)


def _read_loop():
    global _reader_stop
    while not _reader_stop and _connected():
        try:
            raw = motors_serial.ser.readline()
            if raw:
                print(raw.decode("utf-8", errors="replace"), end="", flush=True)
        except Exception:
            break
        time.sleep(0.01)


def start_serial_reader():
    global _reader_stop
    if not _ensure_serial():
        return
    _reader_stop = False
    threading.Thread(target=_read_loop, daemon=True).start()


def _exit_actuator_unlocked():
    global _in_actuator, _moving, _current_actuator
    if _moving:
        _send_char("s")
        time.sleep(0.05)
        _moving = False
    if _in_actuator and _connected():
        _send_char("o")
        time.sleep(0.05)
        _in_actuator = False
        _current_actuator = None


def exit_actuator():
    """Send o so Arduino leaves runActuator and flip works again."""
    with _actuator_lock:
        _exit_actuator_unlocked()
    return {"status": "ok", "message": "Exited actuator"}


def start_move(actuator: int, speed: int, direction: str):
    global _in_actuator, _moving, _current_actuator

    if not _ensure_serial():
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

    with _actuator_lock:
        _exit_actuator_unlocked()

        _send_char(str(actuator))
        time.sleep(0.05)
        _in_actuator = True
        _current_actuator = actuator

        _send_char(str(speed))
        time.sleep(0.02)
        _send_char(action)
        _moving = True

    return {
        "status": "ok",
        "message": f"Moving {action}",
        "actuator": actuator,
        "speed": speed,
    }


def stop_move():
    """Stop move and exit actuator so flip motor responds again."""
    with _actuator_lock:
        _exit_actuator_unlocked()
    return {"status": "ok", "message": "Actuator stopped"}


def step_once(actuator: int, speed: int, direction: str = "forward"):
    global _in_actuator, _moving, _current_actuator

    if not _ensure_serial():
        return _err()

    with _actuator_lock:
        _exit_actuator_unlocked()

        _send_char(str(actuator))
        time.sleep(0.05)
        _in_actuator = True
        _current_actuator = actuator

        _send_char(str(speed))
        time.sleep(0.02)
        _send_char("t")
        time.sleep(0.05)

        _send_char("o")
        _in_actuator = False
        _current_actuator = None
        _moving = False

    return {"status": "ok", "message": "Stepped once", "actuator": actuator, "speed": speed}


def main():
    global _reader_stop

    motors_serial.start_serial_program()
    if not _connected():
        print("Not connected")
        return

    start_serial_reader()

    print("Serial Monitor mode (9600)")
    print("  Actuator: 3/4  then  1/2  then  f/b/t  —  s to stop  —  o to exit")
    print("  Flip:     type p, h, cw, ccw, or s  then Enter")
    print("  Quit:     q + Enter")
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
                motors_serial.write_line(cmd)

    finally:
        _reader_stop = True
        exit_actuator()
        motors_serial.stop_serial_program()


if __name__ == "__main__":
    main()
