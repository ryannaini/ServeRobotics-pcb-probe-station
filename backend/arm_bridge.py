# =============================================================
# arm_bridge.py
# =============================================================
# PURPOSE:
#   This is the "tether" between FastAPI (Python) and your C++
#   Kinova controller (.exe).
#
#   FastAPI cannot call C++ functions directly, so this file:
#     1. Starts the C++ program as a subprocess
#     2. Talks to it through stdin/stdout pipes
#     3. Returns simple JSON-style dicts back to main.py
#
# FLOW:
#   React button  →  POST /initialize  →  initialize_robot()
#                                              ↓
#                                    subprocess.Popen(exe --daemon)
#                                              ↓
#                                    C++ runs InitializeRobot()
#                                              ↓
#                                    C++ prints "READY" on stdout
#                                              ↓
#                                    Python reads that line and reports success
# =============================================================

import os
import subprocess
import threading
from collections import deque
from pathlib import Path

# Last lines the C++ daemon wrote to stderr, kept for error messages.
# A background thread has to keep this pipe drained: if it fills up, the
# daemon blocks mid-write and never reaches its "READY" print, which hangs
# /initialize forever.
_stderr_tail = deque(maxlen=100)


def _drain_stderr(pipe):
    for line in iter(pipe.readline, ""):
        _stderr_tail.append(line)
    pipe.close()


# Killing the backend does not kill the daemon it spawned, and that orphan keeps
# the Kinova API session. A second daemon then blocks forever inside the DLL
# without printing anything, so clear any leftover before starting a new one.
def _terminate_orphan_daemons(exe_name):
    subprocess.run(
        ["taskkill", "/F", "/IM", exe_name],
        capture_output=True,
        text=True,
    )


# Upper bound on how long we wait for READY. The daemon normally takes ~15s
# (homing included); anything past this is a hang, and /initialize must answer
# so the UI can leave its "Initializing..." state.
INIT_TIMEOUT_S = 60

# -------------------------------------------------------------
# GLOBAL PROCESS HANDLE
# -------------------------------------------------------------
# _process stores a reference to the running C++ program.
#
# Why we keep it:
#   - InitializeRobot() loads the Kinova DLL and connects once.
#   - We do NOT want to restart the .exe for every button press.
#   - Keeping _process alive means the robot stays connected.
#
# _process.poll() returns:
#   - None  → process is still running
#   - a number → process has exited (that number is the exit code)
# -------------------------------------------------------------
_process = None

# Only one Python caller may use stdin/stdout at a time.
# Without this, /ws/position (coordinates) and /home or /jog interleave
# on the same pipe and steal each other's "done" lines → hung requests
# and a frontend that looks like it "lost connection".
_pipe_lock = threading.Lock()


# -------------------------------------------------------------
# DEFAULT PATHS
# -------------------------------------------------------------
# These are fallback locations if you do not set environment variables.
#
# DEFAULT_EXE:
#   Starting from the project root (__file__) go into Kinova_Ethernet
#   Path to the compiled Visual Studio output (.exe).
#
# DEFAULT_DLL_DIR:
#   Because there is no LoadLibrary path call, Windows has to search for the file.
#   Folder containing CommandLayerEthernet.dll.
#   The C++ code loads that DLL from the "current working directory",
#   so we launch the .exe with cwd set to this folder.
# -------------------------------------------------------------
DEFAULT_EXE = (
    Path(__file__).resolve().parent.parent
    / "Kinova_EthernetController-armcontroller"
    / "Debug"
    / "Kinova_EthernetController.exe"
)

DEFAULT_DLL_DIR = (
    Path(__file__).resolve().parent.parent
    / "JACO-SDK"
    / "API"
    / "x86"
)


def initialize_robot():
    """
    Start the C++ controller (if not already running) and wait until
    it reports READY.

    Returns a dict that FastAPI sends back to React as JSON, for example:
      {"status": "ok", "message": "Robot initialized"}
      {"status": "error", "message": "...", "detail": "..."}
    """
    global _process

    # ---------------------------------------------------------
    # STEP 1: If C++ is already running, do not start it again.
    # ---------------------------------------------------------
    if _process is not None and _process.poll() is None:
        return {"status": "ok", "message": "Robot already initialized"}

    # ---------------------------------------------------------
    # STEP 2: Resolve paths.
    # ---------------------------------------------------------
    # os.environ.get(...) lets you override paths without editing code:
    #   set ARM_CONTROLLER_EXE=C:\path\to\Kinova_EthernetController.exe
    #   set ARM_DLL_DIR=C:\path\to\dll\folder
    exe = Path(os.environ.get("ARM_CONTROLLER_EXE", DEFAULT_EXE))
    dll_dir = Path(os.environ.get("ARM_DLL_DIR", DEFAULT_DLL_DIR))

    # Fail early with a clear message if the .exe has not been built yet.
    if not exe.exists():
        return {
            "status": "error",
            "message": f"C++ executable not found: {exe}",
        }

    # ---------------------------------------------------------
    # STEP 3: Start the C++ program.
    # ---------------------------------------------------------
    # subprocess.Popen is Python's way of saying:
    #   "Windows, please launch this program now."
    #
    # Equivalent to running in cmd:
    #   cd <dll_dir>
    #   Kinova_EthernetController.exe --daemon
    #
    # Arguments explained:
    #   [str(exe), "--daemon"]
    #       → argv[0] = exe path
    #       → argv[1] = "--daemon" (C++ main() uses this to pick daemon mode)
    #
    #   stdin=subprocess.PIPE
    #       → Python can later write commands to C++ via _process.stdin
    #
    #   stdout=subprocess.PIPE
    #       → Python reads C++ output (cout) via _process.stdout
    #
    #   stderr=subprocess.PIPE
    #       → Python can read C++ error/debug output separately
    #
    #   text=True
    #       → treat pipe data as strings, not raw bytes
    #
    #   cwd=...
    #       → working directory for the child process (important for DLL loading)
    # ---------------------------------------------------------
    _terminate_orphan_daemons(exe.name)

    _process = subprocess.Popen(
        [str(exe), "--daemon"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(dll_dir if dll_dir.exists() else exe.parent),
    )

    _stderr_tail.clear()
    threading.Thread(target=_drain_stderr, args=(_process.stderr,), daemon=True).start()

    # Killing the daemon closes its stdout, which unblocks the readline below.
    timed_out = threading.Event()

    def _give_up(proc):
        timed_out.set()
        proc.kill()

    watchdog = threading.Timer(INIT_TIMEOUT_S, _give_up, args=(_process,))
    watchdog.start()

    # ---------------------------------------------------------
    # STEP 4: Wait for C++ to finish InitializeRobot().
    # ---------------------------------------------------------
    # InitializeRobot() prints several diagnostic lines (e.g. "API RESULT: 1",
    # "Serial Number: ...") BEFORE finally printing "READY" or "ERROR". A single
    # readline() would just grab the first diagnostic line and wrongly report
    # failure, so we keep reading lines and ignore anything that isn't one of
    # the two actual signal words the C++ daemon protocol defines.
    # ---------------------------------------------------------
    response = ""
    try:
        while True:
            line = _process.stdout.readline()
            if not line:
                # Empty string from readline() means the pipe closed, i.e. the
                # C++ process exited/crashed before ever sending a real signal.
                response = ""
                break
            response = line.strip()
            if response in ("READY", "ERROR"):
                break
            # Otherwise it's just a diagnostic/debug line — ignore and keep reading.
    finally:
        watchdog.cancel()

    if timed_out.is_set():
        _process = None
        return {
            "status": "error",
            "message": f"Robot did not report READY within {INIT_TIMEOUT_S}s",
            "detail": "".join(_stderr_tail),
        }

    if response != "READY":
        # If we got here, init failed or printed something unexpected.
        stderr = "".join(_stderr_tail)
        _process = None
        return {
            "status": "error",
            "message": f"InitializeRobot failed ({response or 'no response'})",
            "detail": stderr,
        }

    # ---------------------------------------------------------
    # STEP 5: Send the arm home (MoveHome) before we call init "done".
    # ---------------------------------------------------------
    # DISABLED for now: daemon mode already runs MoveHome() before printing
    # READY, so sending "home" again from Python can double-home / fight timing.
    # The daemon's stdin/stdout protocol (see main.cpp run_daemon_mode):
    #   Python writes "home\n"  →  C++ calls MoveHome(result)
    #   C++ prints "done"       →  homing finished successfully
    # ---------------------------------------------------------
    # _process.stdin.write("home\n")
    # _process.stdin.flush()
    #
    # # Same issue as above: MoveHome() prints its own diagnostic lines (e.g.
    # # "MySetAngularControl: 1") before the daemon loop finally prints "done",
    # # so keep reading past anything that isn't the actual signal.
    # home_response = ""
    # while True:
    #     line = _process.stdout.readline()
    #     if not line:
    #         home_response = ""
    #         break
    #     home_response = line.strip()
    #     if home_response == "done":
    #         break
    #
    # if home_response != "done":
    #     stderr = _process.stderr.read() if _process.stderr else ""
    #     return {
    #         "status": "error",
    #         "message": f"MoveHome failed ({home_response or 'no response'})",
    #         "detail": stderr,
    #     }

    return {"status": "ok", "message": "Robot initialized and homed"}


def cartesian_coordinates():
    if _process is None or _process.poll() is not None:
        return {
            "status": "error",
            "message": "_process not intialized properly",
            "detail": None,
        }

    with _pipe_lock:
        _process.stdin.write("coordinates\n")
        _process.stdin.flush()

        response = ""
        while True:
            line = _process.stdout.readline()
            if not line:
                response = ""
                break
            complete = line.strip()
            if complete == "done":
                break
            response = complete.split()

        if len(response) == 6:
            return {
                "status": "ok",
                "message": {
                    "x": float(response[0]),
                    "y": float(response[1]),
                    "z": float(response[2]),
                    "thetaX": float(response[3]),
                    "thetaY": float(response[4]),
                    "thetaZ": float(response[5]),
                },
            }

        return {
            "status": "error",
            "message": "output not reading all values correctly",
            "detail": None,
        }


def movecommands(dx, dy):
    """
    Map a D-pad delta (dx, dy) to a C++ daemon command and wait for "done".
    Frontend typically sends: right (1,0), left (-1,0), up (0,1), down (0,-1).
    """
    if _process is None or _process.poll() is not None:
        return {
            "status": "error",
            "message": "_process not initialized properly",
            "detail": None,
        }

    if dx == 1 and dy == 0:
        command = "right"
    elif dx == -1 and dy == 0:
        command = "left"
    elif dx == 0 and dy == 1:
        command = "up"
    elif dx == 0 and dy == -1:
        command = "down"
    else:
        return {
            "status": "error",
            "message": f"unsupported jog delta dx={dx}, dy={dy}",
        }

    with _pipe_lock:
        _process.stdin.write(command + "\n")
        _process.stdin.flush()
        print(f"SENDING: {command}")

        while True:
            line = _process.stdout.readline()
            if not line:
                print("GOT: (process closed stdout)")
                return {"status": "error", "message": "process died unexpectedly"}

            line = line.strip()
            print(f"GOT: {line}")

            if line == "done":
                return {"status": "ok", "message": "moved"}
            if line == "error":
                return {"status": "error", "message": f"daemon rejected command '{command}'"}


def movinghome():
    if _process is None or _process.poll() is not None:
        return {
            "status": "error",
            "message": "_process not initialized properly",
            "detail": None,
        }

    print("movinghome: waiting for pipe lock...")
    with _pipe_lock:
        print("movinghome: got lock, sending home")
        _process.stdin.write("home\n")
        _process.stdin.flush()
        print("SENDING: home")

        while True:
            line = _process.stdout.readline()
            if not line:
                print("GOT: (process closed stdout)")
                return {"status": "error", "message": "process died unexpectedly"}

            line = line.strip()
            print(f"GOT: {line}")

            if line == "done":
                return {"status": "ok", "message": "moved"}
            if line == "error":
                return {"status": "error", "message": "daemon rejected command 'home'"}


