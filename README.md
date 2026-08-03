# PCB Probe System

Remote PCB debugging platform for probing in-house circuit boards from a web UI — Kinova Gen2 arm control, live camera stream, and telemetry — so firmware engineers don’t wait on multi-week board shipping.

Built for hardware/software integration work at Serve Robotics.

## Architecture

```
React (Vite)  ──REST / WS / MJPEG──►  FastAPI (Python)
                                          │
                          ┌───────────────┼───────────────┐
                          ▼               ▼               ▼
                    arm_bridge.py     camera.py        relays / I/O
                          │               │
                          ▼               ▼
              Kinova C++ daemon      USB camera (OpenCV /
              (stdin/stdout)         DirectShow)
                          │
                          ▼
                   Kinova Gen2 (Ethernet)
```

- **C++** (`Kinova_EthernetController-armcontroller/`) — robot daemon using Kinova APIs  
- **Python** (`backend/`) — FastAPI + subprocess bridge to the arm, camera stream, optics  
- **React** (`frontend/`) — dashboard: live video, pose telemetry, jog / WASD, focus controls  

## Features

- Arm initialize, home, and XY jog (D-pad + WASD hold-to-move)
- Live Cartesian pose over WebSocket
- MJPEG camera preview in the dashboard
- Autofocus toggle and manual focus step
- In/Out (Z) UI control (frontend; wire to a dedicated backend route as needed)
- CORS-enabled API for local frontend development

## Repo layout

```
pcb-probe-system/
├── backend/
│   ├── main.py          # FastAPI app
│   ├── arm_bridge.py    # C++ daemon IPC (stdin/stdout)
│   ├── camera.py        # OpenCV capture + MJPEG generator
│   └── relays.py        # Relay / signal-path helpers
├── frontend/            # React + Vite UI
└── Kinova_EthernetController-armcontroller/
                         # Kinova C++ controller (build in Visual Studio)
```

## Prerequisites

- Windows (Kinova Ethernet controller + DirectShow camera path)
- Python 3.10+ (3.11/3.14 also used in development)
- Node.js 18+
- Visual Studio (Win32 / Debug build of the Kinova controller)
- Kinova Gen2 reachable on Ethernet
- USB camera (e.g. ELP 4K Zoom)

### Python packages

```bash
pip install fastapi uvicorn opencv-python pygrabber
```

Optional (device discovery / COM): `wmi`, `comtypes`

### Frontend

```bash
cd frontend
npm install
```

## Run locally

1. **Build & place** the Kinova daemon exe where `arm_bridge.py` expects it (see path in that file).

2. **Start the backend** (from `backend/`):

```bash
python main.py
```

API listens on `http://0.0.0.0:8000` (docs at `/docs`).

3. **Start the frontend**:

```bash
cd frontend
npm run dev
```

Open the Vite URL (usually `http://localhost:5173`), initialize the arm from the landing page, then use the dashboard.

## API (main routes)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/initialize` | Start / connect arm daemon |
| `POST` | `/home` | Move arm home |
| `POST` | `/jog?dx=&dy=` | XY jog step |
| `GET`  | `/stream` | MJPEG camera stream |
| `POST` | `/autofocus?enable=` | Enable / disable autofocus |
| `POST` | `/focus?delta=` | Manual focus step |
| `WS`   | `/ws/position` | Live Cartesian pose JSON |

## Hardware notes

- **Arm:** Ethernet to Kinova Gen2; C++ process kept alive with a pipe lock so coordinate streaming and jog/home don’t steal each other’s `done` lines.
- **Camera:** OpenCV `CAP_DSHOW`; device selected by friendly name (e.g. “zoom”) via pygrabber. Prefer DirectShow over MSMF on Windows.
- **Arduino / actuators / relays:** used for linear motion, signal injection, and scope/DMM path switching (see `relays.py` and related firmware).

## Skills / stack

C++ · Python · FastAPI · React · WebSockets · REST · OpenCV · Kinova API · Arduino / motors · relays · USB & Ethernet integration · subprocess IPC · live video & telemetry

## Status

Active development. Some UI (e.g. In/Out Z slider) may be ahead of the matching backend route; treat `/docs` and the code as source of truth.

## License

Internal / project use unless otherwise specified.
