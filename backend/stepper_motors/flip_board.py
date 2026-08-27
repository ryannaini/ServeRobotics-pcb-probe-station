## Flip Board — shares one serial port with linear actuators (motors_serial)

from stepper_motors import linear_actuators, motors_serial


def _flip_cmd(line: str):
    """Exit actuator menu first, then send flip line command."""
    if not motors_serial.ser or not motors_serial.ser.is_open:
        return {"status": "error", "message": "Not connected to the Arduino"}
    linear_actuators.exit_actuator()
    motors_serial.write_line(line)
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
        linear_actuators.exit_actuator()
        motors_serial.stop_serial_program()


if __name__ == "__main__":
    main()
