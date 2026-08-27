## FASTAPI also wraps a lot of these functions and makes it
## a decorater

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
import arm_bridge
import camera

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

@app.post("/initialize")
def initialize_arm():
    return arm_bridge.initialize_robot()

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

@app.post("/flip")
def flip_180:
    return flip_board.flip_180()

@app.post("/flip/home")
def flip_home:
    return flip_board.flip_home()

@app.post("/flip/stop")
def flip_stop:
    return flip_board.flip_stop()


## Flip/Rotate provides the boolean value of ccw to determine the direction of rotation
## Given though the main.jsx file /rotate?ccw=true or /rotate?ccw=false

@app.post("flip/rotate")
def flip_rotate(ccw: bool):
    if ccw:
        return flip_board.rotate_ccw()
    else:
        return flip_board.rotate_cw()

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
