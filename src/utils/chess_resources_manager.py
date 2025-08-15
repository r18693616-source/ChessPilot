import os
import shutil
import logging
from shutil import which
import sys
from pathlib import Path

from .downloader import download_stockfish

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(ch)

README_STOCKFISH_URL = "https://github.com/OTAKUWeBer/ChessPilot/blob/main/README.md"
README_ONNX_URL = "https://github.com/OTAKUWeBer/ChessPilot/blob/main/README.md"

def find_file_with_keyword(keyword, extension=None, search_path=None):
    """
    Finds the first file in `search_path` containing the keyword in its name
    and optionally matching extension.
    Falls back to current working directory if `search_path` is not provided.
    """
    base_path = Path(search_path or Path.cwd())
    logger.debug(f"Searching for files with keyword '{keyword}' and extension '{extension}' in {base_path}")
    try:
        for file in base_path.iterdir():
            if keyword.lower() in file.name.lower():
                if extension:
                    if file.suffix.lower() == extension.lower():
                        logger.debug(f"Found file: {file}")
                        return file
                else:
                    logger.debug(f"Found file: {file}")
                    return file
    except Exception as e:
        logger.debug(f"Error while scanning {base_path}: {e}")
    logger.debug("No matching file found.")
    return None

def extract_stockfish():
    """
    Ensures a Stockfish binary exists at ./stockfish or ./stockfish.exe in cwd.
    If missing, attempts to download via downloader.download_stockfish().
    Returns True on success (binary available), False otherwise.
    """
    # If bundled by pyinstaller
    bundled_name = "stockfish.exe" if os.name == "nt" else "stockfish"
    if getattr(sys, 'frozen', False):
        bundled_path = Path(sys._MEIPASS) / bundled_name
        if bundled_path.exists():
            logger.info(f"Using bundled Stockfish at {bundled_path}.")
            return True

    # Determine working directory (when called from setup_resources script_dir is typically cwd)
    if getattr(sys, "frozen", False):
        cwd = Path(sys.executable).parent
    else:
        cwd = Path.cwd()
    final_path = cwd / bundled_name

    # If system installed, skip
    system_path = which(bundled_name)
    if system_path:
        logger.info(f"Found system-installed Stockfish at {system_path}. Skipping download/extract.")
        return True

    # If already present in cwd, skip
    if final_path.exists():
        logger.info(f"Stockfish binary already exists at {final_path}. Skipping download.")
        return True

    # Attempt to download using your downloader API
    logger.info(f"Stockfish not found. Attempting to download to {final_path} ...")
    try:
        # Try calling downloader with target path if signature accepts it
        try:
            res = download_stockfish(final_path)
        except TypeError:
            # Fallback: call without args
            logger.debug("download_stockfish() didn't accept a target path; calling without args.")
            res = download_stockfish()

        # Accept several return conventions: True/False, path-like, or None
        if isinstance(res, bool):
            ok = res
        elif res is None:
            # assume downloader performed its own placement; check final_path
            ok = final_path.exists() or which(bundled_name) is not None
        else:
            # if downloader returned a path-like, check it
            try:
                returned = Path(res)
                ok = returned.exists()
                # if it's not at final_path, try moving it into place
                if ok and returned.resolve() != final_path.resolve():
                    try:
                        shutil.move(str(returned), str(final_path))
                        ok = final_path.exists()
                    except Exception as e:
                        logger.warning("Could not move downloaded binary into place: %s", e)
            except Exception:
                ok = False

        if ok:
            # Ensure executable perm on non-windows
            if os.name != "nt":
                try:
                    st = final_path.stat().st_mode
                    final_path.chmod(st | 0o111)
                except Exception as e:
                    logger.warning("Failed to set executable bit: %s", e)
            logger.info(f"Stockfish ready at {final_path}")
            return True
        else:
            logger.error(f"Downloader reported failure or binary not found at {final_path}. See README: {README_STOCKFISH_URL}")
            return False
    except Exception as e:
        logger.exception("Error while attempting to download Stockfish: %s", e)
        return False

def rename_onnx_model():
    """
    Ensures chess_detection.onnx lives in cwd. Searches cwd first, then parent dir.
    """
    cwd = Path.cwd()
    target_name = "chess_detection.onnx"
    target_path = cwd / target_name

    if getattr(sys, 'frozen', False):
        bundled = Path(sys._MEIPASS) / target_name
        if bundled.exists():
            logger.info(f"Using bundled ONNX model at {bundled}.")
            return True
        logger.error(f"ONNX model expected in bundle but not found at {bundled}.")
        return False

    if target_path.exists():
        logger.info(f"ONNX model already exists at {target_path}. Skipping rename.")
        return True

    onnx_file = find_file_with_keyword("chess_detection", ".onnx", search_path=cwd)
    if not onnx_file:
        onnx_file = find_file_with_keyword("chess_detection", ".onnx", search_path=cwd.parent)
    if not onnx_file:
        logger.error(
            f"No ONNX model file found in {cwd} or {cwd.parent}. See README: {README_ONNX_URL}"
        )
        return False

    try:
        shutil.move(str(onnx_file), str(target_path))
        logger.info(f"ONNX model moved to {target_path}")
        return True
    except Exception as e:
        logger.exception("Failed to move ONNX model: %s", e)
        return False

def setup_resources(script_dir: Path, project_dir: Path) -> bool:
    """
    On Windows:
      - ensure Stockfish binary exists (download if missing)
      - move stockfish binary from project_dir->script_dir if present
      - move ONNX model from project_dir->script_dir if present
      - ensure chess_detection.onnx is present in script_dir
    On other OSes: nothing to do.
    Returns True if everything that mattered succeeded.
    """
    if os.name != "nt":
        return True

    # Ensure stockfish binary is present in script_dir (cwd is expected to be script_dir)
    # If the binary exists in the project root, move it into script_dir
    root_bin = project_dir / "stockfish.exe"
    src_bin = script_dir / "stockfish.exe"

    if root_bin.exists() and not src_bin.exists():
        try:
            shutil.move(str(root_bin), str(src_bin))
            logger.info(f"Moved Stockfish binary from project root into src/: {src_bin}")
        except Exception as e:
            logger.warning("Could not move stockfish from project root to src: %s", e)

    # Attempt to ensure stockfish is present (download if missing)
    if not extract_stockfish():
        logger.error("Stockfish setup failed")
        return False

    # ONNX model move & rename: if project had the model, move it to script_dir
    root_onnx = project_dir / "chess_detection.onnx"
    src_onnx = script_dir / "chess_detection.onnx"
    if root_onnx.exists() and not src_onnx.exists():
        try:
            shutil.move(str(root_onnx), str(src_onnx))
            logger.info(f"Copied ONNX model into src/: {src_onnx}")
        except Exception as e:
            logger.warning("Could not move ONNX model from project root: %s", e)

    if not rename_onnx_model():
        logger.error("ONNX rename/move failed")
        return False

    return True

if __name__ == "__main__":
    logger.info("Starting Stockfish download check and ONNX model rename process...")
    # Default behavior: run from cwd (expected to be script_dir)
    script_dir = Path.cwd()
    project_dir = script_dir.parent
    stockfish_ok = extract_stockfish()
    onnx_ok = rename_onnx_model()
    if stockfish_ok and onnx_ok:
        logger.info("Setup complete.")
    else:
        logger.info("Setup incomplete—check errors.")
