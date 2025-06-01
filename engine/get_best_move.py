import os
import subprocess
import shutil
import logging
from tkinter import messagebox

# Logger setup
logger = logging.getLogger("stockfish_engine")
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S")
console_handler.setFormatter(formatter)
logger.handlers = [console_handler]

def get_best_move(depth_var, fen, root=None, auto_mode_var=None):
    try:
        logger.info("Getting best move from Stockfish")
        
        if os.name == "nt":
            stockfish_path = "stockfish.exe"
        else:
            stockfish_path = "stockfish"
            if shutil.which(stockfish_path) is None:
                stockfish_path = "./stockfish"
        
        if not os.path.exists(stockfish_path) and shutil.which(stockfish_path) is None:
            raise FileNotFoundError(f"Stockfish not found at {stockfish_path}")
        
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        logger.debug(f"Using Stockfish path: {stockfish_path}")
        
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
            logger.debug(f"Engine output: {line.strip()}")
            if "score mate" in line:
                try:
                    parts = line.split("score mate")
                    mate_val = int(parts[1].split()[0])
                    if abs(mate_val) == 1:
                        mate_flag = True
                        logger.info("Mate in 1 detected")
                except (IndexError, ValueError):
                    logger.warning("Could not parse mate score")
            if line.startswith("bestmove"):
                best_move = line.strip().split()[1]
                logger.info(f"Best move received: {best_move}")
                break

        updated_fen = None
        if best_move:
            stockfish.stdin.write(f"position fen {fen} moves {best_move}\n")
            stockfish.stdin.write("d\n")
            stockfish.stdin.flush()
            while True:
                line = stockfish.stdout.readline()
                if not line:
                    break
                logger.debug(f"Engine output for new FEN: {line.strip()}")
                if "Fen:" in line:
                    updated_fen = line.split("Fen:")[1].strip()
                    logger.info(f"Updated FEN: {updated_fen}")
                    break
        
        stockfish.stdin.write("quit\n")
        stockfish.stdin.flush()
        stockfish.wait()
        
        return best_move, updated_fen, mate_flag

    except Exception as e:
        logger.error(f"Stockfish error: {str(e)}")
        if root:
            root.after(0, lambda err=e: messagebox.showerror("Error", f"Stockfish error: {str(err)}"))
        if auto_mode_var:
            auto_mode_var.set(False)
        return None, None, False
