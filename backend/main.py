## FASTAPI also wraps a lot of these functions and makes it
## a decorater

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
import arm_bridge
import camera
from stepper_motors import flip_board, linear_actuators

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Open camera once at startup (stored in camera.ctrl for liveStream)
camera.init_camera()

@app.post("/home")
def home_arm():
    print("POST /home received")
    return arm_bridge.movinghome()

@app.post("/jog")
def jog_arm(dx: float = 0, dy: float = 0):
    return arm_bridge.movecommands(dx, dy)

## One velocity pulse per call, same as /jog — the UI repeats it while held.

@app.post("/jog/inout")
def jog_in_out(direction: str):
    return arm_bridge.move_in_out(direction)

@app.post("/retract")
def retract_arm():
    return arm_bridge.retract()

## The UI runs these two as separate steps so it can tick off the arm before
## the boards, instead of staring at one long request with no feedback.

@app.post("/initialize/arm")
def initialize_arm_only():
    return arm_bridge.initialize_robot()


@app.post("/initialize/boards")
def initialize_boards():
    # Close first: a previous session may still hold COM4/COM6, and re-opening
    # a port we already own would just report "already connected".
    linear_actuators.stop_serial_program()
    flip_board.stop_serial_program()

    actuator_status = linear_actuators.start_serial_program()
    flip_status = flip_board.start_serial_program()

    failed = [
        name
        for name, result in (("actuator", actuator_status), ("flip", flip_status))
        if result.get("status") != "ok"
    ]
    return {
        "status": "error" if failed else "ok",
        "message": f"Could not connect: {', '.join(failed)}" if failed else "Both boards connected",
        "actuator": actuator_status,
        "flip": flip_status,
    }


@app.post("/initialize")
def initialize_arm():
    boards = initialize_boards()
    arm_status = arm_bridge.initialize_robot()
    return {**arm_status, "actuator": boards["actuator"], "flip": boards["flip"]}

## ----------------------------------------------------------------
##          C A M E R A     L I V E    S T R E A M

@app.get("/stream")
def live_stream():
    # multipart/x-mixed-replace = MJPEG: browser replaces each part in <img>
    return StreamingResponse(
        camera.liveStream(),
        media_type="multipart/x-mixed-replace; boundary=frame",
)

@app.post("/autofocus")
def toggleautofocus(enable: bool):
    result = camera.toggle_autofocus(enable)
    if result and not result:
        return {"status" : "ok"}
    return {"stauts"  : "error",
            "message" : "Failed to toggle autofocus on/off"}

@app.post("/focus")
def manualfocus(delta: int):
    result = camera.focal_length(delta)
    return result 



## ----------------------------------------------------------------
##          F L I P   B O A R D   C O M M A N D S

@app.post("/flip/180")
def flip_180():
    return flip_board.flip_180()

@app.post("/flip/home")
def flip_home():
    return flip_board.flip_home()

@app.post("/flip/stop")
def flip_stop():
    return flip_board.flip_stop()


## Flip/Rotate provides the boolean value of ccw to determine the direction of rotation
## Given though the main.jsx file /rotate?ccw=true or /rotate?ccw=false

@app.post("/flip/rotate")
def flip_rotate(ccw: bool):
    if ccw:
        return flip_board.rotate_ccw()
    else:
        return flip_board.rotate_cw()


## ----------------------------------------------------------------
##          L I N E A R   A C T U A T O R S
##  Top/Bottom and Slow/Fast live in the UI; serial only fires on move.

@app.post("/actuator/move")
def actuator_move(actuator: int, dir: str, speed: int = 1):
    return linear_actuators.start_move(actuator, speed, dir)


@app.post("/actuator/stop")
def actuator_stop():
    return linear_actuators.stop_move()


@app.post("/actuator/step")
def actuator_step(actuator: int, dir: str = "forward", speed: int = 1):
    return linear_actuators.step_once(actuator, speed, dir)

@app.websocket("/ws/position")
async def stream_position(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message = await asyncio.to_thread(arm_bridge.cartesian_coordinates)
            if message["status"] == "ok":
                data = {"status": "ok", "message": message["message"]}
            else:
                data = {"status": "error", "message": message["message"]}
            await websocket.send_json(data)
            await asyncio.sleep(0.05)
    except Exception:
        return

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
