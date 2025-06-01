from boardreader import get_positions, get_fen_from_position
from engine.capture_screenshot_in_memory import capture_screenshot_in_memory
import logging

logger = logging.getLogger("get current fen")
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S")
console_handler.setFormatter(formatter)
logger.handlers = [console_handler]

def get_current_fen(color_indicator):
    try:
        screenshot = capture_screenshot_in_memory()
        boxes = get_positions(screenshot)
        if boxes:
            _, _, _, fen = get_fen_from_position(color_indicator, boxes)          
            return fen
    except Exception:
        logging.error("Failed to get current FEN", exc_info=True)
        return None