"""Remove the Windows startup launcher for SoundTouchBose."""

from __future__ import annotations

import os
from pathlib import Path


def main() -> None:
    launcher = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / "SoundTouchBose.cmd"
    if launcher.exists():
        launcher.unlink()
        print(f"Removed {launcher}")


if __name__ == "__main__":
    main()
