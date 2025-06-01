import mss
from PIL import Image
import io
from .is_wayland import is_wayland
import subprocess
from tkinter import messagebox
import os
import sys
import shutil
import logging

# Logger setup
logger = logging.getLogger("screenshot")
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S")
console_handler.setFormatter(formatter)
logger.handlers = [console_handler]

def get_binary_path(binary):
    logger.debug(f"Resolving path for binary: {binary}")
    if os.name == "nt" and not binary.endswith(".exe"):
        binary += ".exe"
        
    if getattr(sys, 'frozen', False):
        path = os.path.join(sys._MEIPASS, binary)
        logger.debug(f"Frozen app, binary path: {path}")
    else:
        path = shutil.which(binary)
        if path is None:
            path = binary
        logger.debug(f"Non-frozen, binary resolved to: {path}")

    if not (path and os.path.exists(path)):
        logger.error(f"Binary not found: {binary}")
        messagebox.showerror("Error", f"{binary} is missing! Make sure it's bundled properly.")
        sys.exit(1)
    return path

def capture_screenshot_in_memory(root=None, auto_mode_var=None):
    grim_path = get_binary_path("grim") if is_wayland() else None
    try:
        if is_wayland():
            logger.info("Capturing screenshot using grim (Wayland)...")
            result = subprocess.run([grim_path, "-"], stdout=subprocess.PIPE, check=True)
            image = Image.open(io.BytesIO(result.stdout))
        else:
            logger.info("Capturing screenshot using mss (non-Wayland)...")
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                sct_img = sct.grab(monitor)
                image = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
        logger.debug("Screenshot captured successfully")
        return image
    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        if root:
            root.after(0, lambda err=e: messagebox.showerror("Error", f"Screenshot failed: {str(err)}"))
        if auto_mode_var:
            auto_mode_var.set(False)
        return None
