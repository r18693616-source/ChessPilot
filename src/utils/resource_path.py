import logging
import sys
import os
from pathlib import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def resource_path(relative_path: str) -> str:
    if getattr(sys, 'frozen', False):
        # PyInstaller one‑file unpacked here:
        if hasattr(sys, '_MEIPASS'):
            base = Path(sys._MEIPASS)
        else:
            # one‑dir: look beside the executable
            base = Path(sys.executable).parent
    else:
        # dev: this file lives in src/utils/, so go up two levels to src/
        base = Path(__file__).parent.parent

    full_path = base / relative_path
    logger.debug(f"Resource path for '{relative_path}': {full_path}")
    return str(full_path)
