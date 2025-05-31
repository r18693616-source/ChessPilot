def did_my_piece_move(color_indicator, before_fen: str, after_fen: str, move: str) -> bool:
    """
    Return True iff the only change between before_fen and after_fen
    is that *your* piece moved from move[0:2] → move[2:4].
    """
    # Expand a single FEN row like "3P4" → [' ', ' ', ' ', 'P', ' ', ' ', ' ', ' ']
    def expand_row(row):
        out = []
        for ch in row:
            if ch.isdigit():
                out += [' '] * int(ch)
            else:
                out.append(ch)
        return out
    # Turn the placement part into a flat 64-list
    def fen_to_list(fen):
        rows = fen.split()[0].split('/')
        flat = []
        for r in rows:
            flat += expand_row(r)
        return flat  # len=64
    before_list = fen_to_list(before_fen)
    after_list  = fen_to_list(after_fen)
    # Map algebraic ("e2") → flat index (0=a8 → 63=h1)
    def algebraic_to_index(sq):
        file = ord(sq[0]) - ord('a')         # 0..7
        rank = 8 - int(sq[1])               # '1'→7 down to '8'→0
        return rank * 8 + file
    start_i = algebraic_to_index(move[0:2])
    end_i   = algebraic_to_index(move[2:4])
    my_pieces = 'PNBRQK' if color_indicator == 'w' else 'pnbrqk'
    moved_from   = before_list[start_i] in my_pieces and after_list[start_i] == ' '
    moved_to     = after_list[end_i]   in my_pieces and before_list[end_i] == ' '
    #—and everything else stayed identical:
    unchanged_elsewhere = all(
        (b == a) or idx in (start_i, end_i)
        for idx, (b, a) in enumerate(zip(before_list, after_list))
    )
    return moved_from and moved_to and unchanged_elsewhere