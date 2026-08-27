## Flip Board Mechanism Control Module
import motors_serial


def flip_180():
    if motors_serial.ser and motors_serial.ser.is_open:
        motors_serial.ser.write(b"p\n")
        return {"status": "ok", "message": "Flip 180 degrees"}
    return {"status": "error", "message": "Not connected to the Arduino"}



def flip_home():
    if motors_serial.ser and motors_serial.ser.is_open:
        motors_serial.ser.write(b"h\n")
        return {"status": "ok", "message": "Flip home"}
    return {"status": "error", "message": "Not connected to the Arduino"}


def flip_stop():
    if motors_serial.ser and motors_serial.ser.is_open:
        motors_serial.ser.write(b"s\n")
        return {"status": "ok", "message": "Flip stop"}
    return {"status": "error", "message": "Not connected to the Arduino"}


def rotate_ccw():
    if motors_serial.ser and motors_serial.ser.is_open:
        motors_serial.ser.write(b"ccw\n")
        return {"status": "ok", "message": "Rotate counter-clockwise"}
    return {"status": "error", "message": "Not connected to the Arduino"}


def rotate_cw():
    if motors_serial.ser and motors_serial.ser.is_open:
        motors_serial.ser.write(b"cw\n")
        return {"status": "ok", "message": "Rotate clockwise"}
    return {"status": "error", "message": "Not connected to the Arduino"}


def main():
    motors_serial.start_serial_program()
    if not motors_serial.ser or not motors_serial.ser.is_open:
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
        motors_serial.stop_serial_program()


if __name__ == "__main__":
    main()
    

## Need to add a function to stop the program




