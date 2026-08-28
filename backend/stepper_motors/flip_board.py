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

# The sketch answers every command with one line: "OK <cmd>" or "ERR <reason>".
# A p/h move reports "DONE <cmd> <pos>" later, when the motion actually ends.
ACK_TIMEOUT_S = 1.5


def _read_ack():
    deadline = time.monotonic() + ACK_TIMEOUT_S
    while time.monotonic() < deadline:
        raw = ser.readline()
        if not raw:
            continue
        line = raw.decode("utf-8", errors="replace").strip()
        if line.startswith(("OK", "ERR")):
            return line
        # Anything else is menu text or a late DONE from a previous move
        print(f"[flip] {line}")
    return None


# The sketch refuses a motion command while it is already moving. That is a
# normal outcome (operator pressed twice), not a fault, so it gets its own
# status the UI can show quietly.
BUSY_REASONS = {
    "flipping": "Still flipping — press Stop first",
    "homing": "Returning to home — press Stop first",
    "jogging cw": "Already jogging clockwise",
    "jogging ccw": "Already jogging counterclockwise",
}


def _explain(ack: str, line: str):
    if ack.startswith("ERR busy"):
        reason = ack[len("ERR busy"):].strip()
        return "busy", BUSY_REASONS.get(reason, f"Flip board is busy ({reason})")
    if ack == "ERR overflow":
        return "error", "Command arrived garbled at the flip board"
    if ack == "ERR unknown":
        return "error", f"Flip board did not recognise '{line}'"
    return "error", f"Flip board rejected '{line}': {ack}"


def _flip_cmd(line: str, message: str):
    if not _connected():
        return {"status": "error", "message": "Not connected to the Arduino, flip board"}

    with _lock:
        # Drop anything left over from earlier commands so the ack we read
        # belongs to this one.
        ser.reset_input_buffer()
        ser.write((line + "\n").encode("ascii"))
        ack = _read_ack()

    if ack is None:
        return {"status": "error", "message": f"No response from the flip board for '{line}'"}
    if ack.startswith("ERR"):
        status, explanation = _explain(ack, line)
        return {"status": status, "message": explanation, "ack": ack}
    return {"status": "ok", "message": message, "ack": ack}


def flip_180():
    # Returns as soon as the board accepts it; the move runs in the background
    # and can be cancelled with flip_stop().
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
