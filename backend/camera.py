## Get the camera as a variable, cv2 goes to the OS of
## this device (MicroSoft DirectShow) the the OS
## Kernal Driver Which then connects to the hardware

import cv2
import threading
import subprocess
from pygrabber.dshow_graph import FilterGraph

# Module-level controller used by liveStream() / FastAPI.
# Must live HERE (camera.py), not only in main.py — liveStream looks up `ctrl` in this file.
ctrl = None


class CameraController:
    def __init__(self, source):
        # `source` may be an int (OpenCV index) OR a str (DirectShow device name).
        # PnP list order is NOT the same as OpenCV/DirectShow index order.
        self.source = source
        self.cam = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def get_jpeg_frame(self):
        ret, frame = self.cam.read()
        if not ret:
            return None
        flag, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not flag:
            return None
        return buffer.tobytes()

    ## Now need a function that handles focus steps 
    def manual_focus(self, step: int):
        global ctrl
        if not toggle_autofocus:
            print("Please turn off autofocus to use manual focusing")
            return
        ctrl.set(cv2.CAP_PROP_FOCUS, step)
        return 

autofocus_on = True 
def toggle_autofocus(enable: bool):
    global ctrl
    if ctrl is not None:
        if enable:
            ctrl.cam.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            autofocus_on = True 
            return True
        else:
            ctrl.cam.set(cv2.CAP_PROP_AUTOFOCUS, 0)
            autofocus_on = False 
            return False
    return None 

def focal_length(delta):
    if autofocus_on is True or None:
        return {"staus"     : "error",
                "message"   : "autofocus is on"}
    global ctrl
    focus = ctrl.cam.get(cv2.CAP_PROP_FOCUS)
    focus = max(0, min(255, focus + delta))
    ctrl.cam.set(cv2.CAP_PROP_FOCUS, focus)
    return {"status"        : "ok"}



def init_camera():
    """Open the camera once and store it in module-level `ctrl`."""
    global ctrl
    if ctrl is not None:
        return ctrl
    
    devices = FilterGraph().get_input_devices()
    idx = 0
    for i, name in enumerate(devices):
        print(i,name)
        if "zoom" in name.lower():
            idx = i

    if idx is None:
        print("[ERROR] No camera found. Make sure the ELP camera is plugged in.")
        return None
    ctrl = CameraController(idx)  # use the source find_camera actually verified
    print(f"[camera] opened source={idx!r}")
    return ctrl


def liveStream():
    """
    MJPEG generator for StreamingResponse.
    Each yield is one multipart part: headers + JPEG bytes.
    """
    global ctrl  ## Calling a Global Ctrl
    if ctrl is None:
        init_camera()
    if ctrl is None:
        return

    while True:
        ret, frame = ctrl.cam.read()
        if not ret:
            print("[ERROR] frame not transferred to computer")
            return

        flag, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
        if not flag:
            return

        jpg = buffer.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n"
        )



