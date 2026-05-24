"""Runtime helpers shared by the application and settings UI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def resource_path(name: str) -> Path:
    return Path(__file__).resolve().parent / "resources" / name


def sync_autostart(enabled: bool) -> None:
    script = "install_autostart.py" if enabled else "uninstall_autostart.py"
    script_path = Path(__file__).resolve().parents[1] / "scripts" / script
    if sys.platform.startswith("win") and script_path.exists():
        subprocess.run([sys.executable, str(script_path)], check=False)
