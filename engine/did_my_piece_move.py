import logging

# Logger setup
logger = logging.getLogger("move_check")
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S")
console_handler.setFormatter(formatter)
logger.handlers = [console_handler]

def did_my_piece_move(color_indicator, before_fen: str, after_fen: str, move: str) -> bool:
    """
    Return True iff the only change between before_fen and after_fen
    is that *your* piece moved from move[0:2] → move[2:4].
    """
    logger.debug(f"Checking move: {move} for color: {color_indicator}")
    
    def expand_row(row):
        out = []
        for ch in row:
            if ch.isdigit():
                out += [' '] * int(ch)
            else:
                out.append(ch)
        return out

    def fen_to_list(fen):
        rows = fen.split()[0].split('/')
        flat = []
        for r in rows:
            flat += expand_row(r)
        return flat

    before_list = fen_to_list(before_fen)
    after_list  = fen_to_list(after_fen)

    def algebraic_to_index(sq):
        file = ord(sq[0]) - ord('a')
        rank = 8 - int(sq[1])
        return rank * 8 + file

    start_i = algebraic_to_index(move[0:2])
    end_i   = algebraic_to_index(move[2:4])
    my_pieces = 'PNBRQK' if color_indicator == 'w' else 'pnbrqk'

    moved_from = before_list[start_i] in my_pieces and after_list[start_i] == ' '
    moved_to   = after_list[end_i]   in my_pieces and before_list[end_i] == ' '

    unchanged_elsewhere = all(
        (b == a) or idx in (start_i, end_i)
        for idx, (b, a) in enumerate(zip(before_list, after_list))
    )

    if moved_from and moved_to and unchanged_elsewhere:
        logger.info(f"Valid move by player: {move}")
        return True
    else:
        logger.warning(
            f"Move check failed: moved_from={moved_from}, moved_to={moved_to}, unchanged_elsewhere={unchanged_elsewhere}"
        )
        return False
