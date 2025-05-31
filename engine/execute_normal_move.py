import time
from boardreader import get_positions, get_fen_from_position
from engine.capture_screenshot_in_memory import capture_screenshot_in_memory
from engine.get_current_fen import get_current_fen
from engine.chess_notation_to_index import chess_notation_to_index
from engine.move_piece import move_piece
from engine.did_my_piece_move import did_my_piece_move

def execute_normal_move(
    board_positions,
    color_indicator,
    move,
    mate_flag,
    expected_fen,
    root,
    auto_mode_var,
    update_status,
    btn_play
):
    """
    Try up to 3 times to drag your piece; only succeed if
    did_my_piece_move(before_fen, current_fen, move) is True.
    
    Parameters:
      - board_positions: dict mapping (col,row) -> screen‐coordinates
      - color_indicator: "w" or "b"
      - move:           string like "e2e4"
      - mate_flag:      bool (if True, we display "Checkmate" and turn off auto mode)
      - expected_fen:   (unused in this implementation, but kept as placeholder)
      - root:           Tk root (so we can call root.after for any messageboxes)
      - auto_mode_var:  tk.BooleanVar (so we can set it to False on errors/mate)
      - update_status:  callback function update_status(str) to update your status_label
    """
    
    max_retries = 3

    for attempt in range(1, max_retries + 1):
        # 1) Grab the current FEN before moving
        original_fen = get_current_fen(color_indicator)
        if not original_fen:
            time.sleep(0.1)
            continue

        # 2) Convert “e2e4” (or similar) into (start_col,start_row),(end_col,end_row)
        start_idx, end_idx = chess_notation_to_index(
            color_indicator,
            root,
            auto_mode_var,
            move
        )
        if start_idx is None or end_idx is None:
            # Invalid notation → chess_notation_to_index already popped up an error box
            time.sleep(0.1)
            continue

        # 3) Look up the pixel‐coordinates of those squares
        try:
            start_pos = board_positions[start_idx]
            end_pos   = board_positions[end_idx]
        except KeyError:
            # Our board_positions dictionary didn’t contain that square → retry
            time.sleep(0.1)
            continue

        # 4) Drag / move the piece on screen
        move_piece(color_indicator, move, board_positions, auto_mode_var, root, btn_play)
        time.sleep(0.1)

        # 5) Take a fresh screenshot and read the new FEN
        img = capture_screenshot_in_memory()
        if not img:
            # Screenshot failed → retry
            continue

        boxes = get_positions(img)
        if not boxes:
            # Couldn’t detect board → retry
            continue

        try:
            _, _, _, current_fen = get_fen_from_position(color_indicator, boxes)
        except ValueError:
            # FEN extraction error → retry
            continue

        # 6) Check if our move actually took place
        if did_my_piece_move(color_indicator, original_fen, current_fen, move):
            # The move registered successfully on the GUI
            last_fen = current_fen.split()[0]
            status = f"Best Move: {move}\nMove Played: {move}"
            if mate_flag:
                status += "\n𝘾𝙝𝙚𝙘𝙠𝙢𝙖𝙩𝙚"
                auto_mode_var.set(False)
            # Update the status label in your Tk window
            update_status(status)
            return True

    # If we reach here, all retries failed
    update_status(f"Move failed to register after {max_retries} attempts")
    auto_mode_var.set(False)
    return False
