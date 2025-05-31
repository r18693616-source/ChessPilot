import os
import subprocess
import shutil
from tkinter import messagebox

def get_best_move(depth_var, fen, root=None, auto_mode_var=None):
    try:
        # Determine the Stockfish engine executable path based on the OS.
        if os.name == "nt":
            stockfish_path = "stockfish.exe"
        else:
            # Try to locate stockfish in PATH
            stockfish_path = "stockfish"
            if shutil.which(stockfish_path) is None:
                # Fall back to the executable in the current directory
                stockfish_path = "./stockfish"
        flags = 0
        if os.name == "nt":
            flags = subprocess.CREATE_NO_WINDOW
        stockfish = subprocess.Popen(
            [stockfish_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=flags
        )
        stockfish.stdin.write(f"position fen {fen}\n")
        stockfish.stdin.write(f"go depth {depth_var}\n")
        stockfish.stdin.flush()
        best_move = None
        mate_flag = False
        while True:
            line = stockfish.stdout.readline()
            if not line:
                break
            if "score mate" in line:
                try:
                    parts = line.split("score mate")
                    mate_val = int(parts[1].split()[0])
                    if abs(mate_val) == 1:
                        mate_flag = True
                except (IndexError, ValueError):
                    pass
            if line.startswith("bestmove"):
                best_move = line.strip().split()[1]
                break
        updated_fen = None
        if best_move:
            stockfish.stdin.write(f"position fen {fen} moves {best_move}\n")
            stockfish.stdin.write("d\n")
            stockfish.stdin.flush()
            while True:
                line = stockfish.stdout.readline()
                if "Fen:" in line:
                    updated_fen = line.split("Fen:")[1].strip()
                    break
        stockfish.stdin.write("quit\n")
        stockfish.stdin.flush()
        stockfish.wait()
        return best_move, updated_fen, mate_flag
    except Exception as e:
        root.after(0, lambda err=e: messagebox.showerror("Error", f"Stockfish error: {str(err)}"))
        auto_mode_var.set(False)
        return None, None, False