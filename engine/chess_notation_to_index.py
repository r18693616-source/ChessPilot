from tkinter import messagebox

def chess_notation_to_index(color_indicator, root, auto_mode_var, move):
    if color_indicator == "w":
        col_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
        row_map = {'1': 7, '2': 6, '3': 5, '4': 4, '5': 3, '6': 2, '7': 1, '8': 0}
    else:
        col_map = {'a': 7, 'b': 6, 'c': 5, 'd': 4, 'e': 3, 'f': 2, 'g': 1, 'h': 0}
        row_map = {'1': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6, '8': 7}

    try:
        # Expect move to be at least 4 chars: "<file><rank><file><rank>"
        start_col = col_map[move[0]]
        start_row = row_map[move[1]]
        end_col   = col_map[move[2]]
        end_row   = row_map[move[3]]
        return (start_col, start_row), (end_col, end_row)

    except (KeyError, IndexError):
        # Invalid notation: show error box and turn off auto mode
        root.after(
            0,
            lambda: messagebox.showerror(
                "Error", f"Invalid move notation: {move}"
            )
        )
        auto_mode_var.set(False)
        return None, None
