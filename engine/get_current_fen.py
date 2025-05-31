from boardreader import get_positions, get_fen_from_position
from engine.capture_screenshot_in_memory import capture_screenshot_in_memory

def get_current_fen(color_indicator):
    try:
        screenshot = capture_screenshot_in_memory()
        boxes = get_positions(screenshot)
        if boxes:
            _, _, _, fen = get_fen_from_position(color_indicator, boxes)
            return fen
    except Exception:
        return None