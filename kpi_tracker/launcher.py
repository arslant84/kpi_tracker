"""
KPI Tracker — standalone Windows app launcher.

Starts Django in a background thread, then opens a native WebView2 window.
Closing the window exits the app cleanly.
"""

import os
import sys
import socket
import threading
import time
from pathlib import Path


def _hide_console() -> None:
    """Suppress the console window immediately — gives a pure desktop-app feel."""
    if sys.platform == 'win32':
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE


def _setup_logging() -> None:
    """Write stdout/stderr to a log file next to the exe (useful for support)."""
    if getattr(sys, 'frozen', False):
        log = Path(sys.executable).parent / 'kpi_tracker.log'
        f = open(log, 'w', buffering=1, encoding='utf-8')
        sys.stdout = f
        sys.stderr = f


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def wait_for_server(port: int, timeout: int = 60) -> bool:
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=1)
            return True
        except Exception:
            time.sleep(0.3)
    return False


def run_django(port: int) -> None:
    from django.core.management import call_command
    call_command('runserver', f'127.0.0.1:{port}', '--noreload')


def main() -> None:
    _hide_console()
    _setup_logging()

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kpi_tracker.settings')

    if getattr(sys, 'frozen', False):
        bundle = Path(sys._MEIPASS)
        if str(bundle) not in sys.path:
            sys.path.insert(0, str(bundle))

    print('KPI Tracker starting...')

    import django
    django.setup()

    from django.core.management import call_command
    print('Checking database...')
    call_command('migrate', verbosity=0, interactive=False)

    from django.contrib.auth.models import User
    if not User.objects.filter(is_superuser=True).exists():
        User.objects.create_superuser('admin', '', 'admin')
        print('First run — login: admin / admin')

    port = find_free_port()
    print(f'Starting server on port {port}...')

    threading.Thread(target=run_django, args=(port,), daemon=True).start()

    if not wait_for_server(port):
        print('ERROR: server did not start.')
        return

    print(f'Server ready. Opening window...')

    import webview
    webview.create_window(
        title='KPI Tracker',
        url=f'http://127.0.0.1:{port}/',
        width=1400,
        height=900,
        min_size=(1024, 600),
    )
    webview.start()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        # If no log file, show a message box
        if sys.platform == 'win32':
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, str(e), 'KPI Tracker Error', 0x10)
