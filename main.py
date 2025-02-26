import pyautogui
import time
from pathlib import Path
import subprocess
import mss
import mss.tools
import sys
import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import threading
import shutil
from boardreader import get_fen_from_position
from boardreader import get_positions


def get_stockfish_path():
    # If the app is bundled (e.g., with PyInstaller)
    if getattr(sys, 'frozen', False):
        path = os.path.join(sys._MEIPASS, "stockfish.exe" if os.name == "nt" else "stockfish")
    else:
        if os.name == "nt":
            path = "stockfish.exe"
        else:
            # For Linux, try to find stockfish in the PATH
            path = shutil.which("stockfish")
            # If not found in PATH, fallback to a relative name
            if path is None:
                path = "stockfish"

    # Verify that the path exists and is executable
    if not (path and os.path.exists(path)):
        messagebox.showerror("Error", "Stockfish is missing! Make sure it's bundled properly.")
        sys.exit(1)

    return path

stockfish_path = get_stockfish_path()


def resource_path(relative_path):
    try:
        # PyInstaller stores data files in sys._MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class ChessAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess Assistant")
        # Increase window size to accommodate castling options nicely
        self.root.geometry("350x300")
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)  # Prevent minimization
        self.color_indicator = None
        self.last_automated_click_time = 0

        # Configure dark theme colors
        self.bg_color = "#2e2e2e"
        self.btn_color = "#3e3e3e"
        self.text_color = "#ffffff"
        self.accent_color = "#4CAF50"

        self.root.configure(bg=self.bg_color)
        
        # Set the window icon
        self.set_window_icon()
        
        # Create GUI elements
        self.create_color_selection()
        self.create_main_interface()
        self.show_color_selection()

        # Bind Esc key to handle_esc_key method
        self.root.bind('<Escape>', self.handle_esc_key)
    
    def set_window_icon(self):
        """Sets the window icon to 'chess-logo.png' if found, otherwise uses the default Tk icon."""
        logo_path = resource_path(os.path.join('assets', 'chess-logo.png'))
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                self.icon = ImageTk.PhotoImage(img)
                self.root.iconphoto(False, self.icon)
            except Exception as e:
                print(f"Could not set icon from {logo_path}: {e}")
    
    def handle_esc_key(self, event=None):
        """Switch back to color selection when Esc is pressed."""
        if self.main_frame.winfo_ismapped():
            self.main_frame.pack_forget()
            self.color_frame.pack(expand=True, fill=tk.BOTH, pady=20)
            self.color_indicator = None
            self.btn_play.config(state=tk.DISABLED)
            self.update_status("")

    def create_color_selection(self):
        self.color_frame = tk.Frame(self.root, bg=self.bg_color)
        self.lbl_color = tk.Label(self.color_frame, 
                                  text="Select Your Color:",
                                  bg=self.bg_color,
                                  fg=self.text_color,
                                  font=('Arial', 12))
        self.btn_white = tk.Button(self.color_frame,
                                   text="White",
                                   command=lambda: self.set_color("w"),
                                   bg=self.accent_color,
                                   fg=self.text_color,
                                   width=10)
        self.btn_black = tk.Button(self.color_frame,
                                   text="Black",
                                   command=lambda: self.set_color("b"),
                                   bg=self.accent_color,
                                   fg=self.text_color,
                                   width=10)

    def create_main_interface(self):
        self.main_frame = tk.Frame(self.root, bg=self.bg_color)
        self.btn_play = tk.Button(self.main_frame,
                                  text="Play Next Move",
                                  command=self.process_move_thread,
                                  bg=self.accent_color,
                                  fg=self.text_color,
                                  state=tk.DISABLED)
        self.status_label = tk.Label(self.main_frame,
                                     text="",
                                     bg=self.bg_color,
                                     fg=self.text_color,
                                     wraplength=300,
                                     anchor="center",
                                     justify="center")
        
        self.btn_play.pack(pady=10)
        # Create castling options UI (both independent)
        self.create_castling_options()        
        self.status_label.pack(pady=10, fill=tk.BOTH, expand=True)
        self.main_frame.grid_propagate(False)

    def create_castling_options(self):
        """Creates two independent checkboxes for castling options with improved layout."""
        self.castling_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        
        # BooleanVars default to False (unticked)
        self.kingside_var = tk.BooleanVar(value=False)
        self.queenside_var = tk.BooleanVar(value=False)
        
        # Create checkbuttons with a fixed width so text fits nicely.
        self.kingside_cb = tk.Checkbutton(self.castling_frame,
                                          text="Kingside Castle",
                                          variable=self.kingside_var,
                                          bg=self.bg_color,
                                          fg=self.text_color,
                                          selectcolor=self.accent_color,
                                          activebackground=self.bg_color,
                                          activeforeground=self.text_color,
                                          font=('Arial', 10),
                                          width=16)
        self.queenside_cb = tk.Checkbutton(self.castling_frame,
                                           text="Queenside Castle",
                                           variable=self.queenside_var,
                                           bg=self.bg_color,
                                           fg=self.text_color,
                                           selectcolor=self.accent_color,
                                           activebackground=self.bg_color,
                                           activeforeground=self.text_color,
                                           font=('Arial', 10),
                                           width=16)
        # Arrange the checkbuttons using grid.
        self.kingside_cb.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.queenside_cb.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.castling_frame.pack(pady=10)

    def show_color_selection(self):
        self.color_frame.pack(expand=True, fill=tk.BOTH, pady=20)
        self.lbl_color.pack(pady=5)
        self.btn_white.pack(pady=5)
        self.btn_black.pack(pady=5)

    def set_color(self, color):
        self.color_indicator = color
        self.color_frame.pack_forget()
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=20)
        self.btn_play.config(state=tk.NORMAL)
        self.update_status(f"Playing as {'White' if color == 'w' else 'Black'}")

    def update_status(self, message):
        self.status_label.config(text=message)
        self.root.update()

    def capture_screenshot(self, path):
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                sct_img = sct.grab(monitor)
                mss.tools.to_png(sct_img.rgb, sct_img.size, output=str(path))
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Screenshot failed: {e}")
            return False

    def get_best_move(self, fen):
        try:
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
            stockfish.stdin.write("go depth 15\n")
            stockfish.stdin.flush()
            
            output = ""
            while True:
                line = stockfish.stdout.readline()
                if line.startswith("bestmove"):
                    output = line.strip()
                    break

            stockfish.stdin.write("quit\n")
            stockfish.stdin.flush()
            stockfish.wait()
            return output.split()[1] if output else None
        except Exception as e:
            messagebox.showerror("Error", f"Stockfish error: {e}")
            return None

    def chess_notation_to_index(self, move):
        if self.color_indicator == "w":
            col_map = {'a':0, 'b':1, 'c':2, 'd':3, 'e':4, 'f':5, 'g':6, 'h':7}
            row_map = {'1':7, '2':6, '3':5, '4':4, '5':3, '6':2, '7':1, '8':0}
        else:
            col_map = {'a':7, 'b':6, 'c':5, 'd':4, 'e':3, 'f':2, 'g':1, 'h':0}
            row_map = {'1':0, '2':1, '3':2, '4':3, '5':4, '6':5, '7':6, '8':7}
        
        try:
            start_col = col_map[move[0]]
            start_row = row_map[move[1]]
            end_col = col_map[move[2]]
            end_row = row_map[move[3]]
            return (start_col, start_row), (end_col, end_row)
        except KeyError:
            messagebox.showerror("Error", f"Invalid move notation: {move}")
            return None, None

    def move_piece(self, move, board_positions):
        start_idx, end_idx = self.chess_notation_to_index(move)
        if not start_idx or not end_idx:
            return

        try:
            start_pos = board_positions[start_idx]
            end_pos = board_positions[end_idx]
        except KeyError:
            messagebox.showerror("Error", "Could not map move to board positions")
            return

        start_x, start_y = start_pos
        end_x, end_y = end_pos

        pyautogui.click(start_x, start_y)
        self.last_automated_click_time = time.time()
        time.sleep(0.25)
        pyautogui.click(end_x, end_y)
        self.last_automated_click_time = time.time()
        self.update_status(f"Executed move: {move}")

    def expand_fen_row(self, row):
        """Expands a FEN row string by replacing digits with that many spaces."""
        expanded = ""
        for char in row:
            if char.isdigit():
                expanded += " " * int(char)
            else:
                expanded += char
        return expanded

    def is_castling_possible(self, fen, color, side):
        """
        Checks if the king and the corresponding rook are in their original positions
        based on the FEN's piece placement. Returns True if castling is physically possible.
        """
        board = fen.split()[0]
        rows = board.split('/')
        if color == "w":
            # For white, the king should be on e1.
            last_row = self.expand_fen_row(rows[-1])
            if len(last_row) != 8 or last_row[4] != 'K':
                return False
            if side == 'kingside':
                return last_row[7] == 'R'
            elif side == 'queenside':
                return last_row[0] == 'R'
        else:
            # For black, the king should be on e8.
            first_row = self.expand_fen_row(rows[0])
            if len(first_row) != 8 or first_row[4] != 'k':
                return False
            if side == 'kingside':
                return first_row[7] == 'r'
            elif side == 'queenside':
                return first_row[0] == 'r'
        return False

    def update_fen_castling_rights(self, fen):
        """
        Updates the castling availability field of the FEN.
        For each side (white and black), if castling is physically possible and (for the player's side)
        the corresponding checkbox is ticked, the right is added.
        Otherwise, only the opponent's rights (if any) are taken from the board.
        If no rights are available, a '-' is used.
        """
        fields = fen.split()
        # fields[0]: board, fields[1]: active color, fields[2]: current castling rights, etc.
        # Recalculate castling rights:
        white_castling = ""
        # White kingside:
        if self.is_castling_possible(fen, "w", "kingside"):
            if self.color_indicator == "w":
                if self.kingside_var.get():
                    white_castling += "K"
            else:
                white_castling += "K"
        # White queenside:
        if self.is_castling_possible(fen, "w", "queenside"):
            if self.color_indicator == "w":
                if self.queenside_var.get():
                    white_castling += "Q"
            else:
                white_castling += "Q"

        black_castling = ""
        # Black kingside:
        if self.is_castling_possible(fen, "b", "kingside"):
            if self.color_indicator == "b":
                if self.kingside_var.get():
                    black_castling += "k"
            else:
                black_castling += "k"
        # Black queenside:
        if self.is_castling_possible(fen, "b", "queenside"):
            if self.color_indicator == "b":
                if self.queenside_var.get():
                    black_castling += "q"
            else:
                black_castling += "q"

        new_castling = white_castling + black_castling
        if new_castling == "":
            new_castling = "-"
        fields[2] = new_castling
        return " ".join(fields)

    def process_move(self):
        self.root.after(0, lambda: self.update_status("Processing move..."))

        try:
            # Capture screenshot
            screenshot_path = Path("chess-screenshot.png")
            if screenshot_path.exists():
                screenshot_path.unlink()

            if not self.capture_screenshot(screenshot_path):
                self.root.after(0, lambda: self.update_status("Screenshot failed!"))
                return

            # Get detections from the image
            boxes = get_positions(screenshot_path)
            if not boxes:
                self.root.after(0, lambda: self.update_status("No pieces detected."))
                return

            try:
                # Get FEN and chessboard data from boardreader
                chessboard_x, chessboard_y, square_size, fen = get_fen_from_position(self.color_indicator, boxes)
            except ValueError as e:
                self.root.after(0, lambda: self.update_status(f"Error: {e}"))
                return

            # Update FEN's castling rights based on board state and ticked options.
            fen = self.update_fen_castling_rights(fen)

            # Compute board positions based on chessboard data
            board_size = 8
            board_positions = {}
            for row in range(board_size):
                for col in range(board_size):
                    x = chessboard_x + col * square_size + (square_size / 2)
                    y = chessboard_y + row * square_size + (square_size / 2)
                    board_positions[(col, row)] = (x, y)

            # Get best move from Stockfish with the updated FEN.
            best_move = self.get_best_move(fen)
            if not best_move:
                self.root.after(0, lambda: self.update_status("No valid move found!"))
                return

            # If Stockfish recommends castling, execute it automatically if allowed.
            castling_moves = {"e1g1", "e1c1", "e8g8", "e8c8"}
            if best_move in castling_moves:
                side = 'kingside' if best_move in {"e1g1", "e8g8"} else 'queenside'
                # Only execute castling if the corresponding checkbox is ticked and FEN indicates it's possible.
                if ((side == 'kingside' and self.kingside_var.get()) or (side == 'queenside' and self.queenside_var.get())):
                    if self.is_castling_possible(fen, self.color_indicator, side):
                        self.move_piece(best_move, board_positions)
                        self.root.after(0, lambda: self.update_status(f"Best Move: {best_move}\nCastling move executed: {best_move}"))
                        return

            # Otherwise, execute the best move as returned.
            self.move_piece(best_move, board_positions)
            self.root.after(0, lambda: self.update_status(f"Best Move: {best_move}\nMove Played: {best_move}"))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred:\n{e}"))

    def process_move_thread(self):
        threading.Thread(target=self.process_move, daemon=True).start()
    
if __name__ == "__main__":
    root = tk.Tk()
    app = ChessAssistant(root)
    root.mainloop()