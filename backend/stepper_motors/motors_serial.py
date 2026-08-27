## This file will be used whenever we initialize the website and close down the website
## such that motor and the flip board do not need to handle the serial communication

import threading
import time

import serial
import serial.tools.list_ports

FLIP_ARDUINO = "16C153BB515453484D202020FF0B2515"

ser = None
_lock = threading.Lock()


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
        return {"status": "error", "message": f"Motor Arduino not found ({FLIP_ARDUINO})"}

    try:
        ser = serial.Serial(port, 9600, timeout=1)
    except serial.SerialException as e:
        print(f"Could not open {port}: {e}")
        print("Another program still has this port — check for:")
        print("  - another flip_board.py terminal waiting at input")
        print("  - python.exe in Task Manager")
        print("  - Arduino Serial Monitor")
        print("Run:  taskkill /F /IM python.exe")
        return {"status": "error", "message": f"Could not open {port}: {e}"}

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


def write_bytes(data: bytes):
    """Thread-safe serial write — one port shared by flip + actuators."""
    if not ser or not ser.is_open:
        return False
    with _lock:
        ser.write(data)
        ser.flush()
    return True


def write_char(ch: str):
    if len(ch) != 1:
        return False
    return write_bytes(ch.encode("ascii"))


def write_line(line: str):
    return write_bytes((line.strip() + "\n").encode("ascii"))