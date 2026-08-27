"""
Serial Monitor replica for motor_controller.ino.

Type exactly what you would in the Arduino Serial Monitor:
  Actuator: 3 or 4  →  1 or 2  →  f / b / t  →  s (while moving)  →  o (exit)
  Flip:     p / h / cw / ccw / s  then Enter (line + newline)

Actuator chars are sent one byte at a time (no newline).
Flip commands are sent as a line ending in \\n.
"""

import threading
import time

import motors_serial


_reader_stop = False


def _connected():
    return bool(motors_serial.ser and motors_serial.ser.is_open)


def _send_char(ch: str):
    if not _connected() or len(ch) != 1:
        return False
    motors_serial.ser.write(ch.encode("ascii"))
    motors_serial.ser.flush()
    return True


def _send_line(line: str):
    if not _connected():
        return False
    motors_serial.ser.write((line.strip() + "\n").encode("ascii"))
    motors_serial.ser.flush()
    return True


def _read_loop():
    """Print everything the Arduino sends — same as Serial Monitor."""
    global _reader_stop
    while not _reader_stop and _connected():
        try:
            raw = motors_serial.ser.readline()
            if raw:
                print(raw.decode("utf-8", errors="replace"), end="", flush=True)
        except Exception:
            break
        time.sleep(0.01)


def main():
    global _reader_stop

    motors_serial.start_serial_program()
    if not _connected():
        print("Not connected")
        return

    _reader_stop = False
    reader = threading.Thread(target=_read_loop, daemon=True)
    reader.start()

    print("Serial Monitor mode (9600)")
    print("  Actuator: 3/4  then  1/2  then  f/b/t  —  s to stop move  —  o to exit")
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

            # Single actuator / move chars — no newline (matches Serial Monitor, no line ending)
            if len(cmd) == 1 and cmd in "3412fbtso":
                _send_char(cmd)
            else:
                # Flip commands — buffered until newline on Arduino
                _send_line(cmd)

    finally:
        _reader_stop = True
        reader.join(timeout=1.0)
        motors_serial.stop_serial_program()


if __name__ == "__main__":
    main()
