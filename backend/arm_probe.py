"""
Diagnostic: run the Kinova daemon directly and timestamp every line it prints.

  python arm_probe.py [seconds]

Shows exactly which step of InitializeRobot() the C++ stops on, since
/initialize only reports success once the daemon prints READY.
"""

import subprocess
import sys
import threading
import time
from pathlib import Path

from arm_bridge import DEFAULT_DLL_DIR, DEFAULT_EXE

start = time.time()


def stamp(stream_name, pipe):
    for line in iter(pipe.readline, ""):
        print(f"[{time.time() - start:6.1f}s {stream_name}] {line.rstrip()}", flush=True)
    print(f"[{time.time() - start:6.1f}s {stream_name}] <pipe closed>", flush=True)


print(f"exe: {DEFAULT_EXE} exists={DEFAULT_EXE.exists()}", flush=True)
print(f"dll: {DEFAULT_DLL_DIR} exists={DEFAULT_DLL_DIR.exists()}", flush=True)

proc = subprocess.Popen(
    [str(DEFAULT_EXE), "--daemon"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    cwd=str(DEFAULT_DLL_DIR if DEFAULT_DLL_DIR.exists() else DEFAULT_EXE.parent),
)

threading.Thread(target=stamp, args=("out", proc.stdout), daemon=True).start()
threading.Thread(target=stamp, args=("err", proc.stderr), daemon=True).start()

timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 90
deadline = start + timeout
while time.time() < deadline:
    if proc.poll() is not None:
        print(f"[{time.time() - start:6.1f}s] exited with code {proc.returncode}", flush=True)
        break
    time.sleep(0.5)
else:
    print(f"[{time.time() - start:6.1f}s] still running — killing", flush=True)
    proc.kill()

time.sleep(0.5)
