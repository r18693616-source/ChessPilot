import logging
import sys
from pathlib import Path
import os
from shutil import which

from .downloader import download_stockfish

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def resource_path(relative_path: str) -> str:
    """
    Resolve a resource path.
    Special-case 'stockfish' on Unix-like systems: check PATH and /usr/bin first;
    if missing, attempt to download via downloader.download_stockfish() and then
    re-check /usr/bin. If downloader returns a path, return that. Raises FileNotFoundError
    only if all attempts fail.
    """
    # Special handling for the stockfish binary on non-windows OSes
    if relative_path.lower() == "stockfish" and os.name != "nt":
        usr_bin = Path("/usr/bin/stockfish")

        # 1) prefer system PATH if available
        system_path = which("stockfish")
        if system_path:
            logger.debug(f"Using system Stockfish from PATH: {system_path}")
            return str(Path(system_path))

        # 2) check /usr/bin
        if usr_bin.exists():
            logger.debug(f"Found Stockfish at {usr_bin}")
            return str(usr_bin)

        # 3) Not found — attempt to call downloader to install into /usr/bin
        logger.info("/usr/bin/stockfish not found. Attempting to download/install Stockfish into /usr/bin ...")
        res = None
        try:
            # prefer passing the target path (downloader may accept Path)
            try:
                logger.debug("Calling download_stockfish with target Path('/usr/bin/stockfish') ...")
                res = download_stockfish(usr_bin)
            except TypeError:
                logger.debug("download_stockfish() doesn't accept a target. Calling without args ...")
                res = download_stockfish()
            logger.debug("Downloader returned: %s", res)
        except Exception as e:
            logger.exception("Downloader call failed: %s", e)
            # re-check in case downloader used sudo and created /usr/bin/stockfish despite exception
            if usr_bin.exists():
                logger.info("Stockfish appeared at /usr/bin after download attempt.")
                return str(usr_bin)
            raise FileNotFoundError("Stockfish not found in PATH or /usr/bin, downloader failed to install") from e

        # After downloader attempt, prefer /usr/bin if present
        if usr_bin.exists():
            logger.info("Stockfish installed at /usr/bin/stockfish")
            return str(usr_bin)

        # If downloader returned a path-like, check it and return if exists
        try:
            if res:
                returned = Path(res)
                if returned.exists():
                    logger.info("Downloader returned a valid path: %s", returned)
                    return str(returned)
        except Exception:
            pass

        # Nothing worked
        raise FileNotFoundError("Stockfish not found in PATH or /usr/bin after download attempt")

    # For frozen apps, prefer bundled resources and external next to exe
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

    # Dev layout: prefer project/src relative path (same as before)
    dev_base = Path(__file__).parent.parent
    dev_path = dev_base / relative_path
    logger.debug(f"Dev resource path for '{relative_path}': {dev_path}")
    return str(dev_path)
