import pyautogui
import time
import subprocess
import mss
import mss.tools
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
import shutil
from boardreader import get_fen_from_position
from boardreader import get_positions


def get_stockfish_path():
    
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
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class ChessPilot:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess Pilot")
        self.root.geometry("350x300")
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)
        self.color_indicator = None
        self.last_automated_click_time = 0
        self.last_fen = ""
        self.depth_var = tk.IntVar(value=15)
        self.auto_mode_var = tk.BooleanVar(value=False)
        self.processing_move = False

        # To store board cropping parameters for auto mode
        self.chessboard_x = None
        self.chessboard_y = None
        self.square_size = None

        # Modern color scheme
        self.bg_color = "#2D2D2D"
        self.frame_color = "#373737"
        self.accent_color = "#4CAF50"
        self.text_color = "#FFFFFF"
        self.hover_color = "#45a049"
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TScale", troughcolor=self.frame_color, background=self.bg_color)
        self.style.configure("TCheckbutton", background=self.bg_color, foreground=self.text_color)
        
        self.set_window_icon()
        self.create_widgets()
        self.root.bind('<Escape>', self.handle_esc_key)

    def set_window_icon(self):
        logo_path = resource_path(os.path.join('assets', 'chess-logo.png'))
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                self.icon = ImageTk.PhotoImage(img)
                self.root.iconphoto(False, self.icon)
            except Exception:
                pass

    def handle_esc_key(self, event=None):
        if self.main_frame.winfo_ismapped():
            self.main_frame.pack_forget()
            self.color_frame.pack(expand=True, fill=tk.BOTH)
            self.color_indicator = None
            self.btn_play.config(state=tk.DISABLED)
            self.update_status("")
            # If auto mode was running, turn it off
            self.auto_mode_var.set(False)
            self.btn_play.config(state=tk.NORMAL)

    def create_widgets(self):
        # Color selection frame
        self.color_frame = tk.Frame(self.root, bg=self.bg_color)
        
        header = tk.Label(self.color_frame, text="Chess Pilot", font=('Segoe UI', 18, 'bold'),
                        bg=self.bg_color, fg=self.accent_color)
        header.pack(pady=(20, 10))

        color_panel = tk.Frame(self.color_frame, bg=self.frame_color, padx=20, pady=15)
        tk.Label(color_panel, text="Select Your Color:", font=('Segoe UI', 11),
                bg=self.frame_color, fg=self.text_color).pack(pady=5)
        
        btn_frame = tk.Frame(color_panel, bg=self.frame_color)
        self.btn_white = self.create_color_button(btn_frame, "White", "w")
        self.btn_black = self.create_color_button(btn_frame, "Black", "b")
        btn_frame.pack(pady=5)

        depth_panel = tk.Frame(color_panel, bg=self.frame_color)
        tk.Label(depth_panel, text="Stockfish Depth:", font=('Segoe UI', 10),
                bg=self.frame_color, fg=self.text_color).pack(anchor='w')
        
        # Set the slider's command to update the label dynamically
        self.depth_slider = ttk.Scale(depth_panel, from_=15, to=30, variable=self.depth_var,
                                    style="TScale", command=self.update_depth_label)
        self.depth_slider.pack(fill='x', pady=5)
        
        # Initialize depth label with the current value
        self.depth_label = tk.Label(depth_panel, text=f"Depth: {self.depth_var.get()}",
                                    font=('Segoe UI', 9), bg=self.frame_color, fg=self.text_color)
        self.depth_label.pack()
        depth_panel.pack(fill='x', pady=10)
        
        color_panel.pack(padx=30, pady=10, fill='x')
        self.color_frame.pack(expand=True, fill=tk.BOTH)

        # Main interface frame
        self.main_frame = tk.Frame(self.root, bg=self.bg_color)
        
        control_panel = tk.Frame(self.main_frame, bg=self.frame_color, padx=20, pady=15)
        self.btn_play = self.create_action_button(control_panel, "Play Next Moves", self.process_move_thread)
        self.btn_play.pack(fill='x', pady=5)
        
        self.castling_frame = tk.Frame(control_panel, bg=self.frame_color)
        self.kingside_var = tk.BooleanVar()
        self.queenside_var = tk.BooleanVar()
        self.create_castling_checkboxes()
        self.castling_frame.pack(pady=10)

        # New Auto Next Move checkbox with the same style as castling checkboxes
        self.auto_mode_check = ttk.Checkbutton(
            control_panel,
            text="Auto Next Move",
            variable=self.auto_mode_var,
            command=self.toggle_auto_mode,
            style="Castling.TCheckbutton"  # Applies the same UI style
        )
        self.auto_mode_check.pack(pady=5, anchor="center")

        self.status_label = tk.Label(control_panel, text="", font=('Segoe UI', 10),
                                    bg=self.frame_color, fg=self.text_color, wraplength=300)
        self.status_label.pack(fill='x', pady=10)
        control_panel.pack(padx=30, pady=20, fill='both', expand=True)
        
        self.main_frame.pack(expand=True, fill=tk.BOTH)

    def update_depth_label(self, value):
        self.depth_label.config(text=f"Depth: {int(float(value))}")
        self.root.update_idletasks()
        
    def create_color_button(self, parent, text, color):
        btn = tk.Button(parent, text=text, font=('Segoe UI', 10, 'bold'),
                       width=10, bd=0, padx=15, pady=8,
                       bg=self.accent_color, fg=self.text_color,
                       activebackground=self.hover_color,
                       activeforeground=self.text_color,
                       command=lambda: self.set_color(color))
        btn.pack(side=tk.LEFT, padx=5)
        return btn

    def create_action_button(self, parent, text, command):
        return tk.Button(parent, text=text, font=('Segoe UI', 11, 'bold'),
                        bg=self.accent_color, fg=self.text_color,
                        activebackground=self.hover_color,
                        activeforeground=self.text_color,
                        bd=0, pady=10, command=command)

    def create_castling_checkboxes(self):
        style = ttk.Style()
        style.configure("Castling.TCheckbutton",
                        background="#373737",  # Default background color
                        foreground="white",  # Default text color
                        font=("Segoe UI", 10))  # Font configuration

        # Set background color to black on hover (no change to text color)
        style.map("Castling.TCheckbutton",
                  background=[('active', '#333131'), ('pressed', '#333131')],
                  foreground=[('active', 'white'), ('pressed', 'white')])
        
        ttk.Checkbutton(self.castling_frame, text="Kingside Castle", 
                        variable=self.kingside_var, style="Castling.TCheckbutton"
                        ).grid(row=0, column=0, padx=10, sticky='w')
        ttk.Checkbutton(self.castling_frame, text="Queenside Castle",
                        variable=self.queenside_var, style="Castling.TCheckbutton"
                        ).grid(row=1, column=0, padx=10, sticky='w')

    def set_color(self, color):
        self.color_indicator = color
        self.color_frame.pack_forget()
        self.main_frame.pack(expand=True, fill=tk.BOTH)
        self.btn_play.config(state=tk.NORMAL)
        self.update_status(f"\nPlaying as {'White' if color == 'w' else 'Black'}")

    def update_status(self, message):
        self.status_label.config(text=message)
        self.depth_label.config(text=f"Depth: {self.depth_var.get()}")
        self.root.update_idletasks()

    def capture_screenshot_in_memory(self):
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                sct_img = sct.grab(monitor)
                # Create a Pillow Image from the raw data
                image = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
            return image
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Screenshot failed: {e}"))
            return None

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
            stockfish.stdin.write(f"go depth {self.depth_var.get()}\n")
            stockfish.stdin.flush()
            
            best_move = None
            mate_flag = False
            while True:
                line = stockfish.stdout.readline()
                if not line:
                    break
                # Parse mate score if available
                if "score mate" in line:
                    try:
                        # Extract the mate value (e.g., in "score mate 2", mate_val will be 2)
                        parts = line.split("score mate")
                        mate_val = int(parts[1].split()[0])
                        # Only flag immediate mate (mate in 1) as checkmate
                        if abs(mate_val) == 1:
                            mate_flag = True
                    except (IndexError, ValueError):
                        pass
                if line.startswith("bestmove"):
                    best_move = line.strip().split()[1]
                    break

            stockfish.stdin.write("quit\n")
            stockfish.stdin.flush()
            stockfish.wait()
            return best_move, mate_flag
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Stockfish error: {e}"))
            return None, False

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
            self.root.after(0, lambda: messagebox.showerror("Error", f"Invalid move notation: {move}"))
            return None, None

    def move_cursor_to_button(self):
        """Moves the cursor to the center of the 'Play Next Moves' button."""
        try:
            # Get button position relative to the screen
            x = self.btn_play.winfo_rootx()
            y = self.btn_play.winfo_rooty()
            width = self.btn_play.winfo_width()
            height = self.btn_play.winfo_height()
            
            # Calculate center position
            center_x = x + (width // 2)
            center_y = y + (height // 2)
            
            # Move mouse to button center
            pyautogui.moveTo(center_x, center_y, duration=0.1)
        except Exception as e:
            print(f"Error moving cursor: {e}")

    def move_piece(self, move, board_positions):
        start_idx, end_idx = self.chess_notation_to_index(move)
        if not start_idx or not end_idx:
            return

        try:
            start_pos = board_positions[start_idx]
            end_pos = board_positions[end_idx]
        except KeyError:
            self.root.after(0, lambda: messagebox.showerror("Error", "Could not map move to board positions"))
            return

        start_x, start_y = start_pos
        end_x, end_y = end_pos

        pyautogui.click(start_x, start_y)
        self.last_automated_click_time = time.time()
        time.sleep(0.25)
        pyautogui.click(end_x, end_y)
        self.last_automated_click_time = time.time()    
        
        if not self.auto_mode_var.get():       
            self.root.after(0, self.move_cursor_to_button)

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
        if self.processing_move:
            return
        self.processing_move = True
        self.root.after(0, lambda: self.btn_play.config(state=tk.DISABLED))
        self.root.after(0, lambda: self.update_status("\nAnalyzing board..."))

        try:
            # Capture the screenshot directly into memory
            screenshot_image = self.capture_screenshot_in_memory()
            if screenshot_image is None:
                self.root.after(0, lambda: self.update_status("Screenshot failed!"))
                return

            # Process the in-memory screenshot to get board positions
            boxes = get_positions(screenshot_image)
            if not boxes:
                self.root.after(0, lambda: self.update_status("\nNo board or pieces detected."))
                self.auto_mode_var.set(False)
                return

            try:
                chessboard_x, chessboard_y, square_size, fen = get_fen_from_position(self.color_indicator, boxes)
            except ValueError as e:
                self.root.after(0, lambda: self.update_status(f"Error: {e}"))
                return

            fen = self.update_fen_castling_rights(fen)

            board_size = 8
            board_positions = {}
            for row in range(board_size):
                for col in range(board_size):
                    x = chessboard_x + col * square_size + (square_size / 2)
                    y = chessboard_y + row * square_size + (square_size / 2)
                    board_positions[(col, row)] = (x, y)

            # Update instance attributes for board geometry
            self.chessboard_x = chessboard_x
            self.chessboard_y = chessboard_y
            self.square_size = square_size

            best_move, mate_flag = self.get_best_move(fen)
            
            if not best_move:
                self.root.after(0, lambda: self.update_status("No valid move found!"))
                return

            castling_moves = {"e1g1", "e1c1", "e8g8", "e8c8"}
            if best_move in castling_moves:
                side = 'kingside' if best_move in {"e1g1", "e8g8"} else 'queenside'
                if ((side == 'kingside' and self.kingside_var.get()) or 
                    (side == 'queenside' and self.queenside_var.get())):
                    if self.is_castling_possible(fen, self.color_indicator, side):
                        self.move_piece(best_move, board_positions)
                        status_msg = f"\nBest Move: {best_move}\nCastling move executed: {best_move}"
                        if mate_flag:
                            status_msg += "\nCheckmate"
                        self.root.after(0, lambda: self.update_status(status_msg))
                        time.sleep(1)  # Allow UI to update

                        # Stop auto mode if checkmate was detected.
                        if mate_flag:
                            self.auto_mode_var.set(False)
                            return

                        screenshot_image_after = self.capture_screenshot_in_memory()
                        if screenshot_image_after is not None:
                            boxes_after_move = get_positions(screenshot_image_after)
                            if boxes_after_move:
                                try:
                                    _, _, _, lastfen = get_fen_from_position(self.color_indicator, boxes_after_move)
                                    self.last_fen = lastfen.split(" ")[0]
                                except ValueError:
                                    pass
                            return

            self.move_piece(best_move, board_positions)
            status_msg = f"Best Move: {best_move}\nMove Played: {best_move}"
            if mate_flag:
                status_msg += "\n𝘾𝙝𝙚𝙘𝙠𝙢𝙖𝙩𝙚"
            self.root.after(0, lambda: self.update_status(status_msg))

            # Stop auto mode if checkmate was detected.
            if mate_flag:
                self.auto_mode_var.set(False)
                return

            # Re-capture the screenshot after making the move to update the board state
            time.sleep(1)  # Allow UI to update
            screenshot_image_after = self.capture_screenshot_in_memory()
            if screenshot_image_after is not None:
                boxes_after_move = get_positions(screenshot_image_after)
                if boxes_after_move:
                    try:
                        _, _, _, lastfen = get_fen_from_position(self.color_indicator, boxes_after_move)
                        self.last_fen = lastfen.split(" ")[0]
                    except ValueError:
                        pass

        except Exception as e:
            error_message = str(e)  # Capture exception message
            self.root.after(0, lambda: self.update_status(f"Error: {error_message}"))
            self.auto_mode_var.set(False)
        finally:
            self.processing_move = False
            if not self.auto_mode_var.get():
                self.root.after(0, lambda: self.btn_play.config(state=tk.NORMAL))


    def process_move_thread(self):
        threading.Thread(target=self.process_move, daemon=True).start()
        
    def toggle_auto_mode(self):
        if self.auto_mode_var.get():
            # Disable the manual play button.
            self.btn_play.config(state=tk.DISABLED)
            # Trigger an initial move to set cropping parameters.
            self.process_move_thread()
            # Start auto loop in a new thread.
            threading.Thread(target=self.auto_move_loop, daemon=True).start()
        else:
            # Auto mode turned off; re-enable manual button.
            self.btn_play.config(state=tk.NORMAL)

    def auto_move_loop(self):
        """Auto mode: Check board state and only move when it changes"""
        
        # Wait until last_fen gets a value
        while self.last_fen == "" and self.auto_mode_var.get():
            time.sleep(0.3)

        while self.auto_mode_var.get():
            if self.processing_move:
                time.sleep(0.3)
                continue

            try:
                screenshot_image = self.capture_screenshot_in_memory()
                if screenshot_image is None:
                    continue

                boxes = get_positions(screenshot_image)
                if not boxes:
                    continue

                chessboard_x, chessboard_y, square_size, current_fen = get_fen_from_position(self.color_indicator, boxes)
                current_fen_pieces = current_fen.split(" ")[0]  # Get just the piece positions

                if current_fen_pieces != self.last_fen:
                    self.last_fen = current_fen_pieces
                    self.process_move_thread()
                    time.sleep(0.2)

                time.sleep(0.2)

            except Exception as e:
                print(f"Auto loop error: {e}")
                time.sleep(0.2)


if __name__ == "__main__":
    root = tk.Tk()
    app = ChessPilot(root)
    root.mainloop()