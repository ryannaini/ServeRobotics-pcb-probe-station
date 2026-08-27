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
_lock = threading.Lock()
_reader_stop = False


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
    global ser
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
    print(f"Connected on {port}")
    return {"status": "ok", "message": f"Connected on {port}"}


def stop_serial_program():
    global ser
    if ser and ser.is_open:
        ser.close()
        print("Serial closed")
    ser = None


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
