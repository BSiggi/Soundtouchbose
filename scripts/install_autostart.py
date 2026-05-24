"""Create a Windows startup launcher for SoundTouchBose."""

from __future__ import annotations

import os
from pathlib import Path


def main() -> None:
    startup = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    startup.mkdir(parents=True, exist_ok=True)
    launcher = startup / "SoundTouchBose.cmd"
    launcher.write_text("@echo off\r\npythonw -m soundtouchbose\r\n", encoding="utf-8")
    print(f"Created {launcher}")


if __name__ == "__main__":
    main()
