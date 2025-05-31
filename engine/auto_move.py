import time
import threading
from boardreader import get_positions, get_fen_from_position
from engine.capture_screenshot_in_memory import capture_screenshot_in_memory
from engine.process_move import process_move

def process_move_thread(
    root,
    color_indicator,
    auto_mode_var,
    btn_play,
    board_positions,
    update_status,
    kingside_var,
    queenside_var,
    update_last_fen_for_color,
    last_fen_by_color,
    screenshot_delay_var,
    processing_move,
):
    threading.Thread(
        target=process_move,
        args=(
            root,
            color_indicator,
            auto_mode_var,
            btn_play,
            board_positions,
            update_status,
            kingside_var,
            queenside_var,
            update_last_fen_for_color,
            last_fen_by_color,
            screenshot_delay_var,
            processing_move,
        ),
        daemon=True,
    ).start()


def auto_move_loop(
    root,
    color_indicator,
    auto_mode_var,
    btn_play,
    board_positions,
    last_fen_by_color,
    screenshot_delay_var,
    processing_move,
    update_status_callback,
    kingside_var,
    queenside_var,
    update_last_fen_for_color
):
    opp_color = 'b' if color_indicator == 'w' else 'w'
    while auto_mode_var.get():
        if processing_move or not board_positions:
            time.sleep(0.5)
            continue
        try:
            screenshot = capture_screenshot_in_memory()
            if not screenshot:
                time.sleep(0.2)
                continue
            boxes = get_positions(screenshot)
            if not boxes:
                time.sleep(0.2)
                continue
            _, _, _, current_fen = get_fen_from_position(color_indicator, boxes)
            parts = current_fen.split()
            if len(parts) < 2:
                time.sleep(0.2)
                continue
            placement, active = parts[0], parts[1]
            if active == opp_color:
                if placement != last_fen_by_color.get(opp_color, ''):
                    last_fen_by_color[opp_color] = placement
                time.sleep(0.2)
                continue
            if active == color_indicator and placement == last_fen_by_color.get(opp_color, ''):
                time.sleep(0.2)
                continue
            last_fen_by_color[opp_color] = placement
            time.sleep(screenshot_delay_var.get())
            process_move_thread(
            root,
            color_indicator,
            auto_mode_var,
            btn_play,
            board_positions,
            update_status_callback,
            kingside_var,         # ?? you need to pass these
            queenside_var,        # ?? variables must come from parameters or outer scope
            update_last_fen_for_color,
            last_fen_by_color,
            screenshot_delay_var,
            processing_move,
        )

            time.sleep(screenshot_delay_var.get())
        except Exception as e:
            root.after(0, lambda err=e: update_status_callback(f"Error: {str(err)}"))
            auto_mode_var.set(False)
            break
