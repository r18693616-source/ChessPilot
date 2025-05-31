import pyautogui
from tkinter import messagebox
from .is_wayland import is_wayland
from input_capture.wayland import WaylandInput
from engine.chess_notation_to_index import chess_notation_to_index
from engine.move_cursor_to_button import move_cursor_to_button

def move_piece(color_indicator, move, board_positions, auto_mode_var, root, btn_play):
    
    start_idx, end_idx = chess_notation_to_index(color_indicator, root, auto_mode_var, move)
    if not start_idx or not end_idx:
        return
    try:
        start_pos = board_positions[start_idx]
        end_pos = board_positions[end_idx]
    except KeyError:
        root.after(0, lambda: messagebox.showerror("Error", "Could not map move to board positions"))
        auto_mode_var.set(False)
        return
    start_x, start_y = start_pos
    end_x, end_y = end_pos
    try:
        if is_wayland():
            client = WaylandInput()
            client.swipe(int(start_x), int(start_y), int(end_x), int(end_y), 0.001)
        else:
            pyautogui.mouseDown(start_x, start_y)
            pyautogui.moveTo(end_x, end_y)
            pyautogui.mouseUp(end_x, end_y)
    except Exception as e:
        root.after(0, lambda err=e: messagebox.showerror("Error", f"Failed to move piece: {str(err)}"))
        auto_mode_var.set(False)
        return
    if not auto_mode_var.get():
        root.after(0, lambda: move_cursor_to_button(root, auto_mode_var, btn_play))
