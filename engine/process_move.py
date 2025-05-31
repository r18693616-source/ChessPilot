from boardreader import get_positions, get_fen_from_position
import tkinter as tk
import time
from engine.capture_screenshot_in_memory import capture_screenshot_in_memory
from engine.get_best_move import get_best_move
from engine.is_castling_possible import is_castling_possible
from engine.update_fen_castling_rights import update_fen_castling_rights
from engine.execute_normal_move import execute_normal_move
from engine.store_board_positions import store_board_positions
from engine.get_current_fen import get_current_fen
from engine.verify_move import verify_move
from engine.move_piece import move_piece


def process_move(
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
    processing_move
):
    if processing_move:
        return
    processing_move = True
    root.after(0, lambda: btn_play.config(state=tk.DISABLED))
    root.after(0, lambda: update_status("\nAnalyzing board..."))
    try:
        screenshot_image = capture_screenshot_in_memory(root, auto_mode_var)
        if not screenshot_image:
            return

        boxes = get_positions(screenshot_image)
        if not boxes:
            root.after(0, lambda: update_status("\nNo board detected"))
            auto_mode_var.set(False)
            return

        try:
            chessboard_x, chessboard_y, square_size, fen = get_fen_from_position(
                color_indicator, boxes
            )
        except ValueError as e:
            root.after(0, lambda err=e: update_status(f"Error: {str(err)}"))
            auto_mode_var.set(False)
            return

        # FIXED: pass color_indicator, kingside_var, queenside_var, and fen
        fen = update_fen_castling_rights(
            color_indicator,
            kingside_var,
            queenside_var,
            fen
        )

        # Store board positions for future moves
        store_board_positions(board_positions, chessboard_x, chessboard_y, square_size)

        # Ask Stockfish for best move (note: get_best_move expects depth_var, fen, root, auto_mode_var)
        # Since depth_var is not passed here, ensure you call get_best_move with correct args when integrating.
        # For now, this line will need depth from your GUI; adjust as needed in your main code.
        best_move, updated_fen, mate_flag = get_best_move(
            root.depth_var.get() if hasattr(root, "depth_var") else 15,
            fen,
            root,
            auto_mode_var
        )

        update_last_fen_for_color(updated_fen)

        if not best_move:
            root.after(0, lambda: update_status("No valid move found!"))
            return

        castling_moves = {"e1g1", "e1c1", "e8g8", "e8c8"}
        if best_move in castling_moves:
            side = 'kingside' if best_move in {"e1g1", "e8g8"} else 'queenside'
            if ((side == 'kingside' and kingside_var.get()) or 
                (side == 'queenside' and queenside_var.get())):
                if is_castling_possible(fen, color_indicator, side):
                    move_piece(color_indicator, best_move, board_positions, auto_mode_var, root, btn_play)
                    status_msg = f"\nBest Move: {best_move}\nCastling move executed: {best_move}"
                    if mate_flag:
                        status_msg += "\n𝘾𝙝𝙚𝙘𝙠𝙢𝙖𝙩𝙚"
                        auto_mode_var.set(False)
                    root.after(0, lambda: update_status(status_msg))
                    time.sleep(0.3)

                    if mate_flag:
                        # For checkmate, verify once before updating.
                        success, _ = verify_move(color_indicator, best_move, updated_fen)
                        if not success:
                            root.after(0, lambda: update_status(f"Move verification failed on checkmate move\nBest Move: {best_move}"))
                        else:
                            fen_after = get_current_fen(color_indicator)
                            if fen_after:
                                last_fen_by_color[color_indicator] = fen_after.split()[0]
                        auto_mode_var.set(False)
                    else:
                        success, _ = verify_move(color_indicator, best_move, updated_fen)
                        if not success:
                            root.after(0, lambda: update_status(f"Move verification failed\nBest Move: {best_move}"))
                            auto_mode_var.set(False)
                        else:
                            fen_after = get_current_fen(color_indicator)
                            if fen_after:
                                last_fen_by_color[color_indicator] = fen_after.split()[0]
        else:
            # Use execute_normal_move with correct signature
            success = execute_normal_move(
                board_positions,
                color_indicator,
                best_move,
                mate_flag,
                updated_fen,
                root,
                auto_mode_var,
                update_status,
                btn_play
            )
            if not success:
                return

    except Exception as e:
        root.after(0, lambda err=e: update_status(f"Error: {str(err)}"))
        auto_mode_var.set(False)
    finally:
        processing_move = False
        if not auto_mode_var.get():
            root.after(0, lambda: btn_play.config(state=tk.NORMAL))
