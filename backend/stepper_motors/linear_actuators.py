"""
Linear actuators ↔ motor_controller.ino

Serial monitor flow (same as website):
  1. Select top/bottom  (stored locally — no serial yet)
  2. Select slow/fast   (stored locally)
  3. f / b / t / s / o  (uses stored prefs → burst to Arduino)

Burst on move: e.g. b"31f" = actuator 3, speed 1, forward
Stop: s then o
"""

import motors_serial

# Globals — set by UI / CLI before any move command
top_or_bottom = None  # "top" or "bottom"
speed = None          # "slow" or "fast"
_moving = False


def _connected():
    return bool(motors_serial.ser and motors_serial.ser.is_open)


def _err(msg="Not connected to the Arduino, linear actuator"):
    return {"status": "error", "message": msg}


def _write(data: bytes):
    if not _connected():
        return False
    motors_serial.ser.write(data)
    motors_serial.ser.flush()
    return True


def _actuator_char():
    if top_or_bottom == "top":
        return "3"
    if top_or_bottom == "bottom":
        return "4"
    return None


def _speed_char():
    if speed == "slow":
        return "1"
    if speed == "fast":
        return "2"
    return None


def _prefs_ready():
    return _actuator_char() is not None and _speed_char() is not None


def select_actuator(actuator_id: int | None = None, top: bool | None = None):
    global top_or_bottom
    if top is not None:
        top_or_bottom = "top" if top else "bottom"
    elif actuator_id == 3:
        top_or_bottom = "top"
    elif actuator_id == 4:
        top_or_bottom = "bottom"
    else:
        return _err("actuator must be 3 (top) or 4 (bottom)")
    return {"status": "ok", "top_or_bottom": top_or_bottom}


def set_speed(speed_val: int | None = None, slow: bool | None = None):
    global speed
    if slow is not None:
        speed = "slow" if slow else "fast"
    elif speed_val == 1:
        speed = "slow"
    elif speed_val == 2:
        speed = "fast"
    else:
        return _err("speed must be 1 (slow) or 2 (fast)")
    return {"status": "ok", "speed": speed}


def _burst(action: str):
    act = _actuator_char()
    spd = _speed_char()
    if not act or not spd:
        return False
    return _write(f"{act}{spd}{action}".encode("ascii"))


def move_linear_actuator_forward(top=None, spd=None):
    """Hold-to-move start. Website calls this on mousedown."""
    global top_or_bottom, speed, _moving
    if top is not None:
        top_or_bottom = top
    if spd is not None:
        speed = spd
    if not _prefs_ready():
        return _err("Select top/bottom and slow/fast first")
    if _moving:
        stop_linear_actuator()
    if not _burst("f"):
        return _err()
    _moving = True
    return {"status": "ok", "message": "Moving forward", "packet": f"{_actuator_char()}{_speed_char()}f"}


def move_linear_actuator_backward(top=None, spd=None):
    global top_or_bottom, speed, _moving
    if top is not None:
        top_or_bottom = top
    if spd is not None:
        speed = spd
    if not _prefs_ready():
        return _err("Select top/bottom and slow/fast first")
    if _moving:
        stop_linear_actuator()
    if not _burst("b"):
        return _err()
    _moving = True
    return {"status": "ok", "message": "Moving backward", "packet": f"{_actuator_char()}{_speed_char()}b"}


def step_linear_actuator(top=None, spd=None):
    global top_or_bottom, speed, _moving
    if top is not None:
        top_or_bottom = top
    if spd is not None:
        speed = spd
    if not _prefs_ready():
        return _err("Select top/bottom and slow/fast first")
    if _moving:
        stop_linear_actuator()
    if not _burst("t"):
        return _err()
    _write(b"o")
    _moving = False
    return {"status": "ok", "message": "Stepped once", "packet": f"{_actuator_char()}{_speed_char()}t"}


def stop_linear_actuator():
    """Hold-to-move stop. Website calls this on mouseup."""
    global _moving
    if not _connected():
        return _err()
    if _moving:
        _write(b"s")
        _write(b"o")
        _moving = False
    return {"status": "ok", "message": "Actuator stopped"}


def exit_actuator():
    return stop_linear_actuator()


def main():
    global top_or_bottom, speed

    ## How TO Use Serial Monitor to send commands to the arduino:
    ## Must Select Top/Bottom first, then set speed, then send command:
    ## f (forward), b (backward), t (step), s (stop actuator), o (exit program)
    ## Globals top_or_bottom + speed are used when f/b/t/s are sent.

    motors_serial.start_serial_program()
    if not _connected():
        print("Not connected")
        return

    print("Pick top/bottom and slow/fast, then f | b | t | s | o | q")

    while not _prefs_ready():
        cmd = input("Select top/bottom or slow/fast: ").strip().lower()
        if cmd == "top":
            top_or_bottom = "top"
            print(f"Actuator: {top_or_bottom}")
        elif cmd == "bottom":
            top_or_bottom = "bottom"
            print(f"Actuator: {top_or_bottom}")
        elif cmd == "slow":
            speed = "slow"
            print(f"Speed: {speed}")
        elif cmd == "fast":
            speed = "fast"
            print(f"Speed: {speed}")
        elif cmd in ("q", "quit", "exit"):
            motors_serial.stop_serial_program()
            return
        else:
            print("Use: top, bottom, slow, or fast")

    print(f"Ready — {top_or_bottom}, {speed}")

    try:
        while True:
            cmd = input(
                "Command f/b/t/s/o (q quit): "
            ).strip().lower()

            if cmd in ("q", "quit", "exit"):
                stop_linear_actuator()
                break

            if cmd in ("f", "forward"):
                ## Hold forward until user releases (Enter in CLI = button release on site)
                move_linear_actuator_forward()
                input("Holding forward — press Enter to stop...")
                stop_linear_actuator()

            elif cmd in ("b", "backward"):
                move_linear_actuator_backward()
                input("Holding backward — press Enter to stop...")
                stop_linear_actuator()

            elif cmd in ("t", "step"):
                print(step_linear_actuator())

            elif cmd in ("s", "stop"):
                print(stop_linear_actuator())

            elif cmd in ("o", "exit"):
                stop_linear_actuator()
                break

            else:
                print("Invalid. Use f, b, t, s, o, or q")

    finally:
        stop_linear_actuator()
        motors_serial.stop_serial_program()


if __name__ == "__main__":
    main()
