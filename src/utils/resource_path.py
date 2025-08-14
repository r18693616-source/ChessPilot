import logging
import sys
from pathlib import Path
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def resource_path(relative_path: str) -> str:
    if relative_path.lower() == "stockfish" and os.name != "nt":
        # Linux/macOS: prefer system PATH
        from shutil import which
        system_path = which("stockfish")
        if system_path:
            logger.debug(f"Using system Stockfish: {system_path}")
            return system_path
        usr_bin = Path.home() / "usr" / "bin" / "stockfish"
        if usr_bin.exists():
            logger.debug(f"Using user-local Stockfish: {usr_bin}")
            return str(usr_bin)
        raise FileNotFoundError("Stockfish not found in PATH or ~/usr/bin")
    
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            bundled = Path(meipass) / relative_path
            if bundled.exists():
                logger.debug(f"Using bundled resource for '{relative_path}': {bundled}")
                return str(bundled)
        exe_folder = Path(sys.executable).parent
        external = exe_folder / relative_path
        logger.debug(f"Using external resource for '{relative_path}': {external}")
        return str(external)

    dev_base = Path(__file__).parent.parent
    dev_path = dev_base / relative_path
    logger.debug(f"Dev resource path for '{relative_path}': {dev_path}")
    return str(dev_path)

