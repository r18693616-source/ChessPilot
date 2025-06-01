import os
import zipfile
from pathlib import Path
import shutil
import logging
from shutil import which

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

README_STOCKFISH_URL = "https://github.com/OTAKUWeBer/ChessPilot/blob/main/README.md"
README_ONNX_URL = "https://github.com/OTAKUWeBer/ChessPilot/blob/main/README.md"

def find_file_with_keyword(keyword, extension=None, search_path=Path.cwd()):
    """
    Finds the first file in `search_path` containing the keyword in its name
    and optionally matching extension.
    """
    logger.debug(f"Searching for files with keyword '{keyword}' and extension '{extension}' in {search_path}")
    for file in search_path.iterdir():
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
    Ensures a Stockfish binary exists at ./stockfish (Unix) or ./stockfish.exe (Windows).
    If not already present, looks for a ZIP containing 'stockfish' in its name and extracts it.
    If neither is found, logs an error referring the user to the README.
    """

    target_name = "stockfish.exe" if os.name == "nt" else "stockfish"
    final_path = Path.cwd() / target_name

    system_path = which(target_name)
    if system_path:
        logger.info(f"Found system-installed Stockfish at {system_path}. Skipping extraction.")
        return True

    if final_path.exists():
        logger.info(f"Stockfish binary already exists at {final_path}. Skipping extraction.")
        return True

    zip_path = find_file_with_keyword("stockfish", ".zip")
    if not zip_path:
        message = (
            "No Stockfish executable found on your PATH or in the project root. "
            "Please install Stockfish (e.g. `pacman -S stockfish` or `apt install stockfish`),\n"
            f"or place a ZIP with “stockfish” in its name into the project root. "
            f"See README for details: {README_STOCKFISH_URL}"
        )
        logger.error(message)
        return False

    extract_to = Path.cwd() / "temp_stockfish_extract"
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
        message = (
            "Extraction succeeded but no Stockfish executable was found inside the ZIP. "
            f"Please verify the contents of the ZIP (see README for correct download): {README_STOCKFISH_URL}"
        )
        logger.error(message)
        shutil.rmtree(extract_to)
        return False

    # Move and rename into place
    shutil.move(str(stockfish_exe), final_path)
    logger.info(f"Stockfish extracted and renamed to {final_path}")

    # On Unix/macOS, ensure execute permissions
    if os.name != "nt":
        try:
            perms = final_path.stat().st_mode
            final_path.chmod(perms | 0o111)
        except Exception as e:
            logger.warning(f"Could not set execute permissions on {final_path}: {e}")

    # Clean up the temporary directory
    shutil.rmtree(extract_to)
    return True



def rename_onnx_model():
    """
    Ensures an ONNX model exists at ./chess_detection.onnx.
    If not already present, looks for any file with 'chess_detection' in its name and '.onnx' extension.
    If neither is found, logs an error referring the user to the README.
    """
    target_path = Path.cwd() / "chess_detection.onnx"

    # If the correctly named model already exists, do nothing
    if target_path.exists():
        logger.info(f"ONNX model already exists at {target_path}. Skipping rename.")
        return True

    # Look for any *.onnx file with 'chess_detection' in its name
    onnx_file = find_file_with_keyword("chess_detection", ".onnx")
    if not onnx_file:
        message = (
            "No ONNX model file found (filename containing 'chess_detection'). "
            f"Please download the ONNX model using the link in the README: {README_ONNX_URL}"
        )
        logger.error(message)
        return False

    # Move or rename into place
    if onnx_file.parent != Path.cwd():
        shutil.move(str(onnx_file), target_path)
    else:
        onnx_file.rename(target_path)

    logger.info(f"ONNX model renamed/moved to {target_path}")
    return True

if __name__ == "__main__":
    logger.info("Starting Stockfish extraction and ONNX model rename process...")
    stockfish_ok = extract_stockfish()
    onnx_ok = rename_onnx_model()
    if stockfish_ok and onnx_ok:
        logger.info("Setup complete.")
    else:
        logger.info("Setup incomplete—please check the above errors and consult the README for download links.")
