import os
import zipfile
from pathlib import Path
import shutil
import logging
from shutil import which
import sys

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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
    for file in base_path.iterdir():
        if keyword.lower() in file.name.lower():
            if extension:
                if file.suffix.lower() == extension.lower():
                    logger.debug(f"Found file: {file}")
                    return file
            else:
                logger.debug(f"Found file: {file}")
                return file
    logger.debug("No matching file found.")
    return None

def extract_stockfish():
    """
    Ensures a Stockfish binary exists at ./stockfish or ./stockfish.exe in cwd.
    Extracts from ZIP in cwd if needed.
    """
    if getattr(sys, 'frozen', False):
        bundled_name = "stockfish.exe" if os.name == "nt" else "stockfish"
        bundled_path = Path(sys._MEIPASS) / bundled_name
        if bundled_path.exists():
            logger.info(f"Using bundled Stockfish at {bundled_path}.")
            return True

    target_name = "stockfish.exe" if os.name == "nt" else "stockfish"
    if getattr(sys, "frozen", False):
        # one‑file bundle: look in the folder containing the .exe
        cwd = Path(sys.executable).parent
    else:
        cwd = Path.cwd()
    final_path = cwd / target_name

    system_path = which(target_name)
    if system_path:
        logger.info(f"Found system-installed Stockfish at {system_path}. Skipping extraction.")
        return True

    if final_path.exists():
        logger.info(f"Stockfish binary already exists at {final_path}. Skipping extraction.")
        return True

    zip_path = find_file_with_keyword("stockfish", ".zip", search_path=cwd)
    if not zip_path:
        logger.error(
            f"No Stockfish executable or ZIP found in {cwd}. See README: {README_STOCKFISH_URL}"
        )
        return False

    extract_to = cwd / "temp_stockfish_extract"
    extract_to.mkdir(exist_ok=True)

    logger.info(f"Extracting Stockfish from {zip_path} …")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)

    stockfish_exe = None
    for path in extract_to.rglob("*"):
        if (
            path.is_file()
            and "stockfish" in path.name.lower()
            and path.suffix.lower() in [".exe", ""]
        ):
            stockfish_exe = path
            break

    if not stockfish_exe:
        logger.error(
            f"Extracted ZIP but no Stockfish binary found in {extract_to}. See README: {README_STOCKFISH_URL}"
        )
        shutil.rmtree(extract_to)
        return False

    shutil.move(str(stockfish_exe), final_path)
    logger.info(f"Stockfish extracted and renamed to {final_path}")
    if os.name != "nt":
        try:
            perms = final_path.stat().st_mode
            final_path.chmod(perms | 0o111)
        except Exception as e:
            logger.warning(f"Could not set execute permissions on {final_path}: {e}")
    shutil.rmtree(extract_to)
    return True

def rename_stockfish():
    """
    Ensures stockfish.zip or the raw stockfish binary lives in cwd.
    Searches cwd first, then parent dir, and moves it into cwd if found.
    """
    if getattr(sys, "frozen", False):
        cwd = Path(sys.executable).parent
    else:
        cwd = Path.cwd()

    # possible names
    zip_name = "stockfish.zip" if os.name == "nt" else "stockfish"
    bin_name = "stockfish.exe" if os.name == "nt" else "stockfish"
    zip_target = cwd / zip_name
    bin_target = cwd / bin_name

    # If already in cwd, nothing to do
    if zip_target.exists() or bin_target.exists():
        logger.info(f"Stockfish ZIP or binary already in {cwd}.")
        return True

    # Look for ZIP in cwd.parent
    parent_zip = find_file_with_keyword("stockfish", ".zip", search_path=cwd.parent)
    if parent_zip:
        shutil.move(parent_zip, zip_target)
        logger.info(f"Copied {parent_zip.name} into {zip_target}.")
        return True

    # Look for raw binary in cwd.parent
    parent_bin = find_file_with_keyword("stockfish", None, search_path=cwd.parent)
    if parent_bin and parent_bin.name.lower().startswith("stockfish"):
        shutil.move(parent_bin, bin_target)
        logger.info(f"Copied {parent_bin.name} into {bin_target}.")
        return True

    logger.warning(f"No stockfish.zip or binary found in {cwd.parent}.")
    # We’ll let extract_stockfish() still do its own search (system PATH, etc.)
    return True

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

    shutil.move(str(onnx_file), str(target_path))
    logger.info(f"ONNX model moved to {target_path}")
    return True

def setup_resources(script_dir: Path, project_dir: Path) -> bool:
    """
    On Windows:
      1) rename_stockfish()
      2) extract_stockfish()
      3) move stockfish.zip/binary from project_dir->script_dir
      4) move ONNX model from project_dir->script_dir
      5) rename_onnx_model()
    On other OSes: nothing to do.
    Returns True if everything that mattered succeeded.
    """
    if os.name != "nt":
        return True

    # 1) stockfish rename & extract
    if not rename_stockfish():
        return False
    if not extract_stockfish():
        return False

    # 2) move any ZIP/binary from root into src
    root_zip = project_dir / "stockfish.zip"
    src_zip = script_dir / "stockfish.zip"
    root_bin = project_dir / "stockfish.exe"
    src_bin = script_dir / "stockfish.exe"

    if root_zip.exists() and not src_zip.exists():
        shutil.move(str(root_zip), str(src_zip))
        logger.info(f"Copied stockfish.zip into src/: {src_zip}")
    elif root_bin.exists() and not src_bin.exists():
        shutil.move(str(root_bin), str(src_bin))
        logger.info(f"Copied Stockfish binary into src/: {src_bin}")

    # 3) ONNX model move & rename
    root_onnx = project_dir / "chess_detection.onnx"
    src_onnx = script_dir / "chess_detection.onnx"
    if root_onnx.exists() and not src_onnx.exists():
        shutil.move(str(root_onnx), str(src_onnx))
        logger.info(f"Copied ONNX model into src/: {src_onnx}")

    if not rename_onnx_model():
        return False

    return True

if __name__ == "__main__":
    logger.info("Starting Stockfish extraction and ONNX model rename process...")
    stockfish_ok = extract_stockfish()
    onnx_ok = rename_onnx_model()
    if stockfish_ok and onnx_ok:
        logger.info("Setup complete.")
    else:
        logger.info("Setup incomplete—check errors.")
