from .is_wayland import is_wayland
import pyautogui
from input_capture.wayland import WaylandInput
from tkinter import messagebox

def move_cursor_to_button(self):
    try:
        x = self.btn_play.winfo_rootx()
        y = self.btn_play.winfo_rooty()
        width = self.btn_play.winfo_width()
        height = self.btn_play.winfo_height()
        center_x = x + (width // 2)
        center_y = y + (height // 2)
        if is_wayland():
            client = WaylandInput()
            client.click(int(center_x), int(center_y))
        else:
            pyautogui.moveTo(center_x, center_y, duration=0.1)
    except Exception as e:
        self.root.after(0, lambda err=e: messagebox.showerror(f"Error", f"Could not relocate the mouse\n{str(err)}"))
        self.auto_mode_var.set(False)