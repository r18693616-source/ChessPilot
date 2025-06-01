import time
import threading
import logging
from boardreader import get_positions, get_fen_from_position
from engine.capture_screenshot_in_memory import capture_screenshot_in_memory
from engine.process_move import process_move

# Configure logger
logger = logging.getLogger("auto_move")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


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
            logger.debug("Currently processing a move; sleeping...")
            time.sleep(0.5)
            continue

        # If we don't know the board positions yet, wait for them to be set
        if not board_positions:
            logger.warning("Board positions not yet initialized; sleeping...")
            time.sleep(0.5)
            continue

        try:
            logger.debug("Capturing screenshot for auto-move")
            screenshot = capture_screenshot_in_memory()
            if not screenshot:
                logger.warning("Screenshot failed; retrying...")
                time.sleep(0.2)
                continue

            boxes = get_positions(screenshot)
            if not boxes:
                logger.warning("Board detection failed; retrying...")
                time.sleep(0.2)
                continue

            _, _, _, current_fen = get_fen_from_position(color_indicator, boxes)
            logger.info(f"FEN extracted: {current_fen}")
            parts = current_fen.split()
            if len(parts) < 2:
                logger.warning("Malformed FEN; retrying...")
                time.sleep(0.2)
                continue

            placement, active = parts[0], parts[1]
            logger.debug(f"Placement: {placement}, Active: {active}")

            # It's still opponent's turn
            if active == opp_color:
                old = last_fen_by_color.get(opp_color)
                # If we've never recorded opponent's FEN, or it changed, update it
                if old is None or placement != old:
                    logger.info("Opponent just moved (or first-time); updating last_fen_by_color for opponent.")
                    last_fen_by_color[opp_color] = placement
                else:
                    logger.debug("Opponent placement unchanged.")
                time.sleep(0.2)
                continue

            # It's our turn
            if active == color_indicator:
                # If we've never recorded opponent's FEN, wait for them to move at least once
                if opp_color not in last_fen_by_color:
                    logger.debug("Our turn detected but no prior opponent-FEN recorded; sleeping...")
                    time.sleep(0.2)
                    continue

                # If opponent's placement hasn't changed since last record, they haven't moved yet
                if placement == last_fen_by_color[opp_color]:
                    logger.debug("It's our turn but opponent hasn't moved; sleeping...")
                    time.sleep(0.2)
                    continue

                # Otherwise, opponent truly moved—update their last-seen placement
                last_fen_by_color[opp_color] = placement
                logger.info("Detected genuine opponent move; will compute our move.")

                # Pause briefly to let the physical board settle
                delay = screenshot_delay_var.get()
                logger.debug(f"Sleeping for delay: {delay}")
                time.sleep(delay)

                # Spawn the process_move thread to actually calculate and send our move
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

                # Record our own placement (in case needed later)
                logger.info(f"Updating last_fen_by_color for our color ({color_indicator}) to: {placement}")
                last_fen_by_color[color_indicator] = placement

                # Sleep again to let our move register visually before next iteration
                logger.debug(f"Sleeping again for delay: {delay}")
                time.sleep(delay)

        except Exception as e:
            logger.error(f"Exception in auto_move_loop: {e}", exc_info=True)
            root.after(0, lambda err=e: update_status_callback(f"Error: {str(err)}"))
            auto_mode_var.set(False)
            break

    logger.info("Exiting auto_move_loop")