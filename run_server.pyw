"""
Gastro SaaS - Server Wrapper
- Runs waitress in a loop with auto-restart on crash
- PID lock file prevents duplicate instances
- Health check kills hung processes
- Use .pyw extension so pythonw.exe runs it without a console window
"""
import atexit
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

BASE_DIR = Path(__file__).resolve().parent
PYTHON = str(BASE_DIR / 'venv' / 'Scripts' / 'python.exe')
STOP_FILE = BASE_DIR / '.stop_server'
PID_FILE = BASE_DIR / '.server.pid'
LOG_FILE = BASE_DIR / 'server.log'
PORT = 8000
HEALTH_CHECK_INTERVAL = 30  # seconds
HEALTH_CHECK_FAILURES_TO_RESTART = 3


def log(msg):
    """Append a timestamped line to the log file."""
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] {msg}\n')
            f.flush()
    except Exception:
        pass


# ============================================================
# PID Lock - prevent duplicate instances
# ============================================================

def acquire_lock():
    """
    Write our PID to the lock file. If another instance is running,
    check if it's actually alive. If alive, exit. If stale, take over.
    """
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            # Check if the old process is still running
            if is_process_alive(old_pid):
                log(f'Otra instancia ya esta corriendo (PID {old_pid}). Saliendo.')
                sys.exit(0)
            else:
                log(f'PID file obsoleto encontrado (PID {old_pid} ya no existe). Tomando control.')
        except (ValueError, OSError):
            pass

    PID_FILE.write_text(str(os.getpid()))
    atexit.register(release_lock)
    log(f'Lock adquirido (PID {os.getpid()})')


def release_lock():
    """Remove the PID file on exit."""
    try:
        if PID_FILE.exists():
            # Only remove if it's our PID
            current = PID_FILE.read_text().strip()
            if current == str(os.getpid()):
                PID_FILE.unlink()
    except Exception:
        pass


def is_process_alive(pid):
    """Check if a process with given PID is running."""
    try:
        os.kill(pid, 0)  # Signal 0 = check existence, don't kill
        return True
    except (OSError, ProcessLookupError):
        return False


# ============================================================
# Port check
# ============================================================

def is_port_in_use(port):
    """Check if a port is already bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False
        except OSError:
            return True


# ============================================================
# Health check
# ============================================================

def health_check_loop(get_proc):
    """
    Periodically ping the server. If it fails multiple times in a row,
    kill the waitress process so the main loop restarts it.
    """
    failures = 0
    # Wait for initial startup
    time.sleep(10)

    while True:
        time.sleep(HEALTH_CHECK_INTERVAL)

        proc = get_proc()
        if proc is None or proc.poll() is not None:
            # Process not running, main loop will handle restart
            failures = 0
            continue

        try:
            resp = urlopen(f'http://127.0.0.1:{PORT}/login/', timeout=10)
            if resp.status == 200:
                failures = 0
                continue
        except Exception:
            pass

        failures += 1
        log(f'Health check fallido ({failures}/{HEALTH_CHECK_FAILURES_TO_RESTART})')

        if failures >= HEALTH_CHECK_FAILURES_TO_RESTART:
            log('Servidor no responde. Reiniciando...')
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            failures = 0


# ============================================================
# Main server loop
# ============================================================

current_proc = None


def get_current_proc():
    return current_proc


def run_server():
    """Start waitress and return when it exits."""
    global current_proc

    log('Iniciando servidor waitress...')

    current_proc = subprocess.Popen(
        [
            PYTHON, '-m', 'waitress',
            '--host=0.0.0.0',
            f'--port={PORT}',
            '--threads=4',
            'pizzeria_saas.wsgi:application',
        ],
        cwd=str(BASE_DIR),
        stdout=open(LOG_FILE, 'a', encoding='utf-8'),
        stderr=subprocess.STDOUT,
    )

    returncode = current_proc.wait()
    log(f'Servidor detenido (code={returncode})')
    current_proc = None
    return returncode


if __name__ == '__main__':
    # 1. Acquire lock (exit if duplicate)
    acquire_lock()

    # 2. Clean stale stop file
    if STOP_FILE.exists():
        STOP_FILE.unlink()

    # 3. Check port
    if is_port_in_use(PORT):
        log(f'ATENCION: Puerto {PORT} ya esta en uso. Intentando continuar...')

    # 4. Start health check thread
    health_thread = threading.Thread(target=health_check_loop, args=(get_current_proc,), daemon=True)
    health_thread.start()

    # 5. Main loop
    consecutive_fast_crashes = 0

    while True:
        start_time = time.time()
        run_server()
        elapsed = time.time() - start_time

        # Check if we should stop
        if STOP_FILE.exists():
            STOP_FILE.unlink()
            log('Stop file detectado. Deteniendo definitivamente.')
            break

        # Track fast crashes (< 5 seconds = probably a config error, not transient)
        if elapsed < 5:
            consecutive_fast_crashes += 1
            if consecutive_fast_crashes >= 5:
                log('ERROR: El servidor crashea inmediatamente (5 veces seguidas). Deteniendo.')
                log('Revisa server.log para ver el error. Ejecuta INSTALAR.bat de nuevo.')
                break
            log(f'Crash rapido #{consecutive_fast_crashes}. Reintentando en 5s...')
            time.sleep(5)
        else:
            consecutive_fast_crashes = 0
            log('Reiniciando servidor en 3s...')
            time.sleep(3)
