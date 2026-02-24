"""
Gastro SaaS - Server Wrapper
Runs waitress in a loop. If the server exits (crash or restart request),
waits 3 seconds and restarts automatically.
Use .pyw extension so pythonw.exe runs it without a console window.
"""
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PYTHON = str(BASE_DIR / 'venv' / 'Scripts' / 'python.exe')
STOP_FILE = BASE_DIR / '.stop_server'
LOG_FILE = BASE_DIR / 'server.log'


def run_server():
    """Start waitress serving the Django app."""
    with open(LOG_FILE, 'a', encoding='utf-8') as log:
        log.write(f'\n[{time.strftime("%Y-%m-%d %H:%M:%S")}] Iniciando servidor...\n')
        log.flush()

        proc = subprocess.run(
            [
                PYTHON, '-m', 'waitress',
                '--host=0.0.0.0',
                '--port=8000',
                '--threads=4',
                'pizzeria_saas.wsgi:application',
            ],
            cwd=str(BASE_DIR),
            stdout=log,
            stderr=log,
        )

        log.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] Servidor detenido (code={proc.returncode})\n')
        log.flush()

    return proc.returncode


if __name__ == '__main__':
    # Remove stale stop file on startup
    if STOP_FILE.exists():
        STOP_FILE.unlink()

    while True:
        run_server()

        # Check if we should stop completely
        if STOP_FILE.exists():
            STOP_FILE.unlink()
            break

        # Otherwise restart after a brief pause
        time.sleep(3)
