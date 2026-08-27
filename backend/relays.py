## Arduino relay board — channel switching (MultiMeter/Oscilloscope)

import time

import serial
import serial.tools.list_ports

ser = None

RELAY_ARDUINO = "8A13C97651534C5036202020FF06113A"


def _find_port(target_serial):
    for port in serial.tools.list_ports.comports():
        if port.serial_number == target_serial:
            return port.device
    return None


def start_relay_program():
    global ser
    if ser and ser.is_open:
        return {"status": "ok", "message": f"Relay already connected on {ser.port}"}

    port = _find_port(RELAY_ARDUINO)
    if not port:
        return {"status": "error", "message": f"Relay Arduino not found ({RELAY_ARDUINO})"}

    try:
        ser = serial.Serial(port, 9600, timeout=1)
        time.sleep(2.0)
        ser.reset_input_buffer()
        print(f"Relay connected on {port}")
        return {"status": "ok", "message": f"Relay connected on {port}"}
    except serial.SerialException as e:
        return {"status": "error", "message": f"Could not open relay port {port}: {e}"}


def stop_relay_program():
    global ser
    if ser and ser.is_open:
        ser.write(b"q")
        ser.close()
        print("Relay serial closed")
    ser = None
    return {"status": "ok", "message": "Relay disconnected"}
