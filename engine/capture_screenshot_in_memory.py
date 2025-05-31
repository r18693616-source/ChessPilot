import mss
from PIL import Image
import io
from .is_wayland import is_wayland
import subprocess
from tkinter import messagebox
import os
import sys
import shutil

def get_binary_path(binary):
    # For Windows, ensure the binary name ends with '.exe'
    if os.name == "nt" and not binary.endswith(".exe"):
        binary += ".exe"
        
    if getattr(sys, 'frozen', False):
        # When bundled with PyInstaller, binaries should be in the _MEIPASS folder
        path = os.path.join(sys._MEIPASS, binary)
    else:
        # Check for binary in system PATH on non-frozen mode
        path = shutil.which(binary)
        if path is None:
            path = binary

    if not (path and os.path.exists(path)):
        messagebox.showerror("Error", f"{binary} is missing! Make sure it's bundled properly.")
        sys.exit(1)
    return path

def capture_screenshot_in_memory(root=None, auto_mode_var=None):
    grim_path = get_binary_path("grim") if is_wayland() else None
    try:
        if is_wayland():
            result = subprocess.run([grim_path, "-"], stdout=subprocess.PIPE, check=True)
            image = Image.open(io.BytesIO(result.stdout))
        else:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                sct_img = sct.grab(monitor)
                image = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
        return image
    except Exception as e:
        if root:
            root.after(0, lambda err=e: messagebox.showerror("Error", f"Screenshot failed: {str(err)}"))
        if auto_mode_var:
            auto_mode_var.set(False)
        return None