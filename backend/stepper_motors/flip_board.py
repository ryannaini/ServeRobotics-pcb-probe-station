## Flip Board — own Arduino, own serial port

import time

import serial
import serial.tools.list_ports

# TODO: paste the flip board Arduino's serial number here
FLIP_ARDUINO = ""

ser = None


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


def _flip_cmd(line: str):
    if not ser or not ser.is_open:
        return {"status": "error", "message": "Not connected to the Arduino"}
    ser.write((line.strip() + "\n").encode("ascii"))
    ser.flush()
    return {"status": "ok", "message": line}


def flip_180():
    return _flip_cmd("p")


def flip_home():
    return _flip_cmd("h")


def flip_stop():
    return _flip_cmd("s")


def rotate_ccw():
    return _flip_cmd("ccw")


def rotate_cw():
    return _flip_cmd("cw")


def main():
    start_serial_program()
    if not ser or not ser.is_open:
        return

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
