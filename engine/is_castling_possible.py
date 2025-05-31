from engine.expend_fen_row import expend_fen_row

def is_castling_possible( fen, color, side):
    board = fen.split()[0]
    rows = board.split('/')
    if color == "w":
        last_row = expend_fen_row(rows[-1])
        if len(last_row) != 8 or last_row[4] != 'K':
            return False
        if side == 'kingside':
            return last_row[7] == 'R'
        elif side == 'queenside':
            return last_row[0] == 'R'
    else:
        first_row = expend_fen_row(rows[0])
        if len(first_row) != 8 or first_row[4] != 'k':
            return False
        if side == 'kingside':
            return first_row[7] == 'r'
        elif side == 'queenside':
            return first_row[0] == 'r'
    return False