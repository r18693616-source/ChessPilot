from engine.is_castling_possible import is_castling_possible

def update_fen_castling_rights(color_indicator,kingside_var, queenside_var, fen):
    fields = fen.split()
    white_castling = ""
    if is_castling_possible(fen, "w", "kingside"):
        if color_indicator == "w":
            if kingside_var.get():
                white_castling += "K"
        else:
            white_castling += "K"
    if is_castling_possible(fen, "w", "queenside"):
        if color_indicator == "w":
            if queenside_var.get():
                white_castling += "Q"
        else:
            white_castling += "Q"
    black_castling = ""
    if is_castling_possible(fen, "b", "kingside"):
        if color_indicator == "b":
            if kingside_var.get():
                black_castling += "k"
        else:
            black_castling += "k"
    if is_castling_possible(fen, "b", "queenside"):
        if color_indicator == "b":
            if queenside_var.get():
                black_castling += "q"
        else:
            black_castling += "q"
    new_castling = white_castling + black_castling
    if new_castling == "":
        new_castling = "-"
    fields[2] = new_castling
    return " ".join(fields)