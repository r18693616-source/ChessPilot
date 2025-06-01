import time
import threading
import logging
from boardreader import get_positions, get_fen_from_position
from engine.capture_screenshot_in_memory import capture_screenshot_in_memory
from engine.process_move import process_move

# Configure logger
logger = logging.getLogger("auto_move")
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S")
console_handler.setFormatter(formatter)
logger.handlers = [console_handler]


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
    logger.info("Starting new thread to process move")
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
    logger.info("Auto move loop started")
    opp_color = 'b' if color_indicator == 'w' else 'w'
    logger.info(f"Player color: {color_indicator}, Opponent color: {opp_color}")
    
    while auto_mode_var.get():
        logger.debug("Loop tick")
        if processing_move:
            logger.info("Currently processing a move, waiting...")
            time.sleep(0.5)
            continue

        if not board_positions:
            logger.warning("Board positions are not available")
            time.sleep(0.5)
            continue

        try:
            logger.debug("Capturing screenshot...")
            screenshot = capture_screenshot_in_memory()
            if not screenshot:
                logger.warning("Failed to capture screenshot")
                time.sleep(0.2)
                continue

            boxes = get_positions(screenshot)
            if not boxes:
                logger.warning("No board positions detected from screenshot")
                time.sleep(0.2)
                continue

            _, _, _, current_fen = get_fen_from_position(color_indicator, boxes)
            logger.info(f"FEN extracted: {current_fen}")
            parts = current_fen.split()
            if len(parts) < 2:
                logger.warning("FEN string is malformed")
                time.sleep(0.2)
                continue

            placement, active = parts[0], parts[1]
            logger.debug(f"Active: {active}, Placement: {placement}")

            if active == opp_color:
                if placement != last_fen_by_color.get(opp_color, ''):
                    logger.info("Opponent moved. Updating last FEN")
                    last_fen_by_color[opp_color] = placement
                else:
                    logger.debug("Opponent position unchanged")
                time.sleep(0.2)
                continue

            if active == color_indicator and placement == last_fen_by_color.get(opp_color, ''):
                logger.debug("It's our turn but no change in opponent FEN. Waiting...")
                time.sleep(0.2)
                continue

            last_fen_by_color[opp_color] = placement
            delay = screenshot_delay_var.get()
            logger.info(f"Ready to move. Waiting for delay: {delay}s")
            time.sleep(delay)

            process_move_thread(
                root,
                color_indicator,
                auto_mode_var,
                btn_play,
                board_positions,
                update_status_callback,
                kingside_var,
                queenside_var,
                update_last_fen_for_color,
                last_fen_by_color,
                screenshot_delay_var,
                processing_move,
            )

            logger.debug("Move processed, sleeping for next cycle...")
            time.sleep(delay)

        except Exception as e:
            logger.error(f"Exception occurred: {e}")
            root.after(0, lambda err=e: update_status_callback(f"Error: {str(err)}"))
            auto_mode_var.set(False)
            break
