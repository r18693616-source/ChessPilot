import time
from boardreader import get_positions, get_fen_from_position
from engine import capture_screenshot_in_memory

def verify_move(color_indicator, _, expected_fen, attempts_limit=3):
    expected_pieces = expected_fen.split()[0]
    for attempt in range(1, attempts_limit + 1):
        if attempt > 1:
            time.sleep(0.2)
        screenshot = capture_screenshot_in_memory()
        if not screenshot:
            continue
        boxes = get_positions(screenshot)
        if not boxes:
            continue
        try:
            _, _, _, current_fen = get_fen_from_position(color_indicator, boxes)
            fen_parts = current_fen.split()
            # If the active color changed, update last FEN and return.
            if len(fen_parts) > 1 and fen_parts[1] != color_indicator:
                last_fen = fen_parts[0]
                return True, attempt
            if fen_parts[0] == expected_pieces:
                last_fen = fen_parts[0]
                return True, attempt
        except ValueError:
            pass
    return False, attempts_limit