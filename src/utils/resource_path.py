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

    Special-case 'stockfish' on Unix-like systems: prefer system PATH, then
    look for a local copy (current working directory, executable folder, or
    dev layout). If missing, attempt to download using downloader.download_stockfish()
    (note: downloader no longer installs to /usr/bin or asks for sudo). After
    the downloader completes we re-check the local locations and also any path
    returned by the downloader. Raises FileNotFoundError only if all attempts fail.
    """
    # Special handling for the stockfish binary on non-windows OSes
    if relative_path.lower() == "stockfish" and os.name != "nt":
        # 1) prefer system PATH if available
        system_path = which("stockfish")
        if system_path:
            logger.debug(f"Using system Stockfish from PATH: {system_path}")
            return str(Path(system_path))

        # 2) check common local locations (cwd, frozen exe dir, dev layout)
        candidates = []

        # if running a frozen app, prefer the executable folder first
        if getattr(sys, 'frozen', False):
            exe_folder = Path(sys.executable).parent
            candidates.append(exe_folder / "stockfish")

        # current working directory
        candidates.append(Path.cwd() / "stockfish")

        # project/dev layout (same as the original fallback)
        dev_base = Path(__file__).parent.parent
        candidates.append(dev_base / "stockfish")

        for c in candidates:
            try:
                if c.exists():
                    logger.debug(f"Found Stockfish locally at: {c}")
                    return str(c)
            except Exception as e:
                logger.warning(f"Could not stat candidate {c}: {e}")

        # 3) Not found — attempt to call downloader (no target; downloader installs next to exe or into CWD)
        logger.info("Stockfish not found in PATH or local dirs. Attempting to download via downloader...")
        res = None
        try:
            try:
                # downloader previously accepted a target; current simplified downloader installs into CWD/exe dir
                logger.debug("Calling download_stockfish() without target...")
                res = download_stockfish()
            except TypeError:
                logger.debug("download_stockfish() raised TypeError; retrying without args")
                res = download_stockfish()
            logger.debug("Downloader returned: %s", res)
        except Exception as e:
            logger.exception("Downloader call failed: %s", e)
            # re-check local candidates in case downloader placed the binary despite the exception
            for c in candidates:
                try:
                    if c.exists():
                        logger.info("Stockfish appeared at %s after download attempt.", c)
                        return str(c)
                except Exception:
                    pass
            raise FileNotFoundError("Stockfish not found in PATH or local dirs; downloader failed") from e

        # After downloader attempt, prefer any candidate that now exists
        for c in candidates:
            try:
                if c.exists():
                    logger.info("Stockfish installed at %s", c)
                    return str(c)
            except Exception:
                pass

        # If downloader returned a path-like, check it and return if it exists
        try:
            if res:
                returned = Path(res)
                if returned.exists():
                    logger.info("Downloader returned a valid path: %s", returned)
                    return str(returned)
        except Exception as e:
            logger.warning("Error checking downloader-returned path: %s", e)

        # Nothing worked
        raise FileNotFoundError("Stockfish not found in PATH or local directories after download attempt")

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
