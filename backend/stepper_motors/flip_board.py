"""
Flip board controller — own Arduino, own serial port.

flip_board.ino takes line commands (text + newline):
  p   = flip 180 degrees (sets new home)
  h   = return to home
  cw  = jog clockwise    (runs until 's')
  ccw = jog counterclockwise
  s   = stop flip jog
"""

import threading
import time

import serial
import serial.tools.list_ports

FLIP_ARDUINO = "19794829515453484D202020FF0B2158"

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

    port = find_arduino_by_serial(FLIP_ARDUINO)
    if not port:
        print(f"Arduino not found (serial {FLIP_ARDUINO})")
        list_ports()
        return {"status": "error", "message": f"Flip Arduino not found ({FLIP_ARDUINO})"}

    try:
        ser = serial.Serial(port, 9600, timeout=1)
    except serial.SerialException as e:
        print(f"Could not open {port}: {e}")
        print("Another program still has this port — check for:")
        print("  - another flip_board.py terminal waiting at input")
        print("  - python.exe in Task Manager")
        print("  - Arduino Serial Monitor")
        return {"status": "error", "message": f"Could not open {port}: {e}"}

    # Opening the port resets the board — wait for setup() before sending
    time.sleep(2.0)
    ser.reset_input_buffer()
    print(f"Connected on {port}")
    return {"status": "ok", "message": f"Connected on {port}"}


def stop_serial_program():
    global ser, _reader_stop
    _reader_stop = True
    if ser and ser.is_open:
        ser.close()
        print("Flip serial closed")
    ser = None


def _connected():
    return bool(ser and ser.is_open)


def _read_loop():
    """Print everything the Arduino sends — same as Serial Monitor."""
    while not _reader_stop and _connected():
        try:
            raw = ser.readline()
            if raw:
                print(raw.decode("utf-8", errors="replace"), end="", flush=True)
        except Exception:
            break
        time.sleep(0.01)


def start_serial_reader():
    global _reader_stop
    if not _connected():
        return
    _reader_stop = False
    threading.Thread(target=_read_loop, daemon=True).start()


## ----------------------------------------------------------------
##          W E B S I T E   A P I

def _flip_cmd(line: str, message: str):
    if not _connected():
        return {"status": "error", "message": "Not connected to the Arduino, flip board"}
    with _lock:
        ser.write((line + "\n").encode("ascii"))
        ser.flush()
    return {"status": "ok", "message": message}


def flip_180():
    # The board blocks until the 180 finishes, so 's' cannot interrupt it
    return _flip_cmd("p", "Flipping 180 degrees")


def flip_home():
    return _flip_cmd("h", "Returning to home")


def flip_stop():
    return _flip_cmd("s", "Flip stopped")


def rotate_cw():
    return _flip_cmd("cw", "Jogging clockwise")


def rotate_ccw():
    return _flip_cmd("ccw", "Jogging counterclockwise")


def main():
    start_serial_program()
    if not _connected():
        print("Not connected")
        return

    start_serial_reader()

    print("Flip Board Mechanism Control Module")
    print("  p   = flip 180 degrees (sets new home)")
    print("  h   = return to home")
    print("  cw  = jog clockwise")
    print("  ccw = jog counterclockwise")
    print("  s   = stop flip jog")
    print("  q   = quit")

    try:
        while True:
            cmd = input("Input a command:> ").strip().lower()
            if cmd in ("q", "quit", "exit"):
                break

            match cmd:
                case "p":
                    print(flip_180())
                case "h":
                    print(flip_home())
                case "cw":
                    print(rotate_cw())
                case "ccw":
                    print(rotate_ccw())
                case "s":
                    print(flip_stop())
                case _:
                    print("Invalid command")
    finally:
        stop_serial_program()


if __name__ == "__main__":
    main()
