from .move_piece_methods import drag_piece, click_piece
from executor.chess_notation_to_index import chess_notation_to_index
from executor.move_cursor_to_button import move_cursor_to_button
from tkinter import messagebox

def move_piece(color_indicator, move, board_positions, auto_mode_var, root, btn_play,
               humanize=True, offset_range=(-16, 16), mode="drag"):
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

    if mode == "drag":
        drag_piece(start_pos, end_pos, humanize, offset_range, root, auto_mode_var)
    elif mode == "click":
        click_piece(start_pos, end_pos, humanize, offset_range, root, auto_mode_var)

    if not auto_mode_var.get():
        root.after(0, lambda: move_cursor_to_button(root, auto_mode_var, btn_play))
