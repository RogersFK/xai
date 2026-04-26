"""
dev.py — XAI Forensics System Development Runner
==================================================
Project structure:
    xai/
    ├── dev.py
    ├── ui/         ← Tkinter frontend (main.py)
    └── api/        ← FastAPI backend  (main.py)

Usage:
    python3 dev.py                  # start both
    python3 dev.py --frontend-only
    python3 dev.py --backend-only
    python3 dev.py --no-watch
"""

import subprocess
import sys
import time
import argparse
import threading
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("[ERROR] watchdog not installed. Run: pip install watchdog")
    sys.exit(1)


# ======================================================================
#  CONFIG
# ======================================================================
ROOT = Path(__file__).parent.resolve()
UI   = ROOT / "ui"
API  = ROOT / "api"

CONFIG = {
    "frontend": {
        "label":  "FRONTEND",
        "color":  "\033[93m",
        "cmd":    [sys.executable, str(UI / "main.py")],
        "cwd":    str(UI),
        "watch":  [str(UI)],
        "strategy": "restart",
    },
    "backend": {
        "label":  "BACKEND ",
        "color":  "\033[96m",
        "cmd":    ["uvicorn", "main:app",
                   "--reload",
                   "--reload-dir", str(API),
                   "--host", "127.0.0.1",
                   "--port", "8000"],
        "cwd":    str(API),
        "watch":  [str(API)],
        "strategy": "uvicorn",
    },
}

RESET = "\033[0m"
RED   = "\033[91m"
GREEN = "\033[92m"
YELLOW= "\033[33m"
DIM   = "\033[2m"


# ======================================================================
#  PROCESS WRAPPER
# ======================================================================
class ManagedProcess:
    def __init__(self, name: str, cmd: list, cwd: str,
                 color: str = "", strategy: str = "restart"):
        self.name     = name
        self.cmd      = cmd
        self.cwd      = cwd
        self.color    = color
        self.strategy = strategy   # "restart" | "uvicorn"
        self.process  = None
        self._stop    = threading.Event()

    # ── start ─────────────────────────────────────────────────────────
    def start(self):
        self._stop.clear()
        self._launch()

    def _launch(self):
        self._log(f"{GREEN}Starting:{RESET} {DIM}{' '.join(str(c) for c in self.cmd)}{RESET}")
        self._log(f"{DIM}cwd: {self.cwd}{RESET}")
        try:
            self.process = subprocess.Popen(
                self.cmd,
                cwd=self.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError as exc:
            self._log(f"{RED}Failed to start: {exc}{RESET}")
            self._log(f"{DIM}Check the command is installed and on PATH.{RESET}")
            return

        t = threading.Thread(target=self._stream, daemon=True)
        t.start()

    def _stream(self):
        try:
            for line in self.process.stdout:
                if self._stop.is_set():
                    break
                print(f"{self.color}[{self.name}]{RESET} {line}", end="",
                      flush=True)
        except Exception:
            pass

    # ── reload ────────────────────────────────────────────────────────
    def reload(self):
        """
        restart  → kill the process and start fresh (Tkinter, plain scripts)
        uvicorn  → uvicorn manages its own reload; we do nothing
        """
        if self.strategy == "uvicorn":
            self._log(f"{DIM}uvicorn handles its own reload — skipping.{RESET}")
            return
        self._log(f"{YELLOW}🔄 Restarting...{RESET}")
        self._kill()
        time.sleep(0.5)
        self._launch()

    # ── kill ──────────────────────────────────────────────────────────
    def _kill(self):
        """Terminate only THIS process, not its entire process group."""
        if not (self.process and self.process.poll() is None):
            return
        self._stop.set()
        try:
            self.process.terminate()        # polite SIGTERM
            self.process.wait(timeout=4)    # wait up to 4 s
        except subprocess.TimeoutExpired:
            self.process.kill()             # force SIGKILL
        except Exception:
            pass

    def stop(self):
        """Public stop — used on shutdown."""
        self._kill()

    def is_alive(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def _log(self, msg: str):
        print(f"{self.color}[{self.name}]{RESET} {msg}", flush=True)


# ======================================================================
#  FILE WATCHER
# ======================================================================
class ChangeHandler(FileSystemEventHandler):
    """
    Watches .py file changes.
    - If the changed file is inside api/  → do nothing (uvicorn self-reloads)
    - If the changed file is inside ui/   → restart frontend
    """
    def __init__(self, processes: dict):
        self._procs = processes
        self._last  = {}   # debounce per-file

    def on_modified(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path).resolve()
        if path.suffix != ".py":
            return
        if "__pycache__" in str(path):
            return

        # debounce — same file within 1.5 s → skip
        now = time.time()
        key = str(path)
        if now - self._last.get(key, 0) < 1.5:
            return
        self._last[key] = now

        print(f"\n{DIM}[WATCHER] Changed: {path}{RESET}", flush=True)
        self._dispatch(path)

    def _dispatch(self, path: Path):
        """Find which process owns this file and trigger its reload."""
        best_name  = None
        best_depth = -1

        for name, cfg in CONFIG.items():
            if name not in self._procs:
                continue
            for watch_dir in cfg["watch"]:
                try:
                    path.relative_to(watch_dir)
                    depth = len(Path(watch_dir).parts)
                    if depth > best_depth:
                        best_depth = depth
                        best_name  = name
                except ValueError:
                    continue

        if best_name:
            self._procs[best_name].reload()
        else:
            print(f"{DIM}[WATCHER] No process matched — skipping.{RESET}",
                  flush=True)


# ======================================================================
#  HELPERS
# ======================================================================
def parse_args():
    p = argparse.ArgumentParser(description="XAI Forensics dev runner")
    p.add_argument("--frontend-only", action="store_true")
    p.add_argument("--backend-only",  action="store_true")
    p.add_argument("--no-watch",      action="store_true")
    return p.parse_args()


def check_paths():
    missing = False
    for path, label in [
        (UI,             "ui/  folder"),
        (UI / "main.py", "ui/main.py"),
        (API,            "api/ folder"),
        (API / "main.py","api/main.py"),
    ]:
        if not path.exists():
            print(f"{RED}[WARN] Missing: {label} → {path}{RESET}", flush=True)
            missing = True
    if missing:
        print(f"{DIM}       Some processes may fail to start.{RESET}\n",
              flush=True)


def banner(mode: str):
    print(f"""
\033[93m╔══════════════════════════════════════════╗
║   XAI Forensics System — Dev Runner      ║
║   Mode: {mode:<33}║
╚══════════════════════════════════════════╝\033[0m
  Root : {ROOT}
  UI   : {UI}
  API  : {API}

  Backend  reload : uvicorn --reload (automatic, hands-off)
  Frontend reload : full restart on .py change

Press Ctrl+C to stop all processes.
""", flush=True)


# ======================================================================
#  MAIN
# ======================================================================
def main():
    args = parse_args()

    run_frontend = not args.backend_only
    run_backend  = not args.frontend_only

    mode = ("Frontend + Backend" if (run_frontend and run_backend)
            else "Frontend only"  if run_frontend
            else "Backend only")

    banner(mode)
    check_paths()

    # build process map
    processes: dict[str, ManagedProcess] = {}

    if run_backend:
        cfg = CONFIG["backend"]
        processes["backend"] = ManagedProcess(
            name=cfg["label"], cmd=cfg["cmd"], cwd=cfg["cwd"],
            color=cfg["color"], strategy=cfg["strategy"],
        )

    if run_frontend:
        cfg = CONFIG["frontend"]
        processes["frontend"] = ManagedProcess(
            name=cfg["label"], cmd=cfg["cmd"], cwd=cfg["cwd"],
            color=cfg["color"], strategy=cfg["strategy"],
        )

    # start all
    for proc in processes.values():
        proc.start()
        time.sleep(0.6)

    # file watcher
    observer = None
    if not args.no_watch:
        handler  = ChangeHandler(processes)
        observer = Observer()
        observer.schedule(handler, str(ROOT), recursive=True)
        observer.start()
        print(f"{DIM}[WATCHER] Active — watching ui/ and api/{RESET}\n",
              flush=True)

    # keep-alive: only auto-restart the frontend if it crashes.
    # Never auto-restart the backend — uvicorn handles itself.
    try:
        while True:
            time.sleep(2)
            for name, proc in processes.items():
                if CONFIG[name]["strategy"] == "uvicorn":
                    continue                 # uvicorn manages itself
                if not proc.is_alive():
                    print(
                        f"{proc.color}[{proc.name}]{RESET} "
                        f"{RED}Exited unexpectedly — restarting in 3 s{RESET}",
                        flush=True,
                    )
                    time.sleep(3)
                    proc.start()

    except KeyboardInterrupt:
        print(f"\n{DIM}[DEV] Shutting down...{RESET}", flush=True)

    finally:
        if observer:
            observer.stop()
            observer.join()
        for proc in processes.values():
            proc.stop()
        print(f"{GREEN}[DEV] All stopped. Goodbye.{RESET}", flush=True)


if __name__ == "__main__":
    main()