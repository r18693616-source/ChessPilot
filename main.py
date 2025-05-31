import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import shutil

from engine.capture_screenshot_in_memory import capture_screenshot_in_memory
from engine.chess_notation_to_index import chess_notation_to_index
from engine.move_cursor_to_button import move_cursor_to_button
from engine.move_piece import move_piece
from engine.expend_fen_row import expend_fen_row
from engine.is_castling_possible import is_castling_possible
from engine.update_fen_castling_rights import update_fen_castling_rights
from engine.did_my_piece_move import did_my_piece_move
from engine.execute_normal_move import execute_normal_move
from engine.process_move import process_move
from engine.store_board_positions import store_board_positions
from engine.verify_move import verify_move
from engine.auto_move import auto_move_loop
from engine.get_best_move import get_best_move
from engine.get_current_fen import get_current_fen

def get_binary_path(binary):
    # For Windows, ensure the binary name ends with '.exe'
    if os.name == "nt" and not binary.endswith(".exe"):
        binary += ".exe"
        
    if getattr(sys, 'frozen', False):
        # When bundled with PyInstaller, binaries should be in the _MEIPASS folder
        path = os.path.join(sys._MEIPASS, binary)
    else:
        # Check for binary in system PATH on non-frozen mode
        path = shutil.which(binary)
        if path is None:
            path = binary

    if not (path and os.path.exists(path)):
        messagebox.showerror("Error", f"{binary} is missing! Make sure it's bundled properly.")
        sys.exit(1)
    return path

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
        self.root.geometry("350x350")
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)

        # Game state variables
        self.color_indicator = None
        self.last_fen = ""
        self.last_fen_by_color = {'w': '', 'b': ''}
        self.depth_var = tk.IntVar(value=15)
        self.auto_mode_var = tk.BooleanVar(value=False)
        self.board_positions = {}
        self.processing_move = False

        # Screenshot delay (0.0 to 1.0 seconds)
        self.screenshot_delay_var = tk.DoubleVar(value=0.4)

        # Board cropping parameters (unused until you set them)
        self.chessboard_x = None
        self.chessboard_y = None
        self.square_size = None

        # UI color scheme
        self.bg_color = "#2D2D2D"
        self.frame_color = "#373737"
        self.accent_color = "#4CAF50"
        self.text_color = "#FFFFFF"
        self.hover_color = "#45a049"
        
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
        """Return to color‐selection screen if ESC is pressed."""
        if self.main_frame.winfo_ismapped():
            self.main_frame.pack_forget()
            self.color_frame.pack(expand=True, fill=tk.BOTH)
            self.color_indicator = None
            self.btn_play.config(state=tk.DISABLED)
            self.update_status("")
            self.auto_mode_var.set(False)
            self.btn_play.config(state=tk.NORMAL)

    def create_widgets(self):
        # Color selection screen
        self.color_frame = tk.Frame(self.root, bg=self.bg_color)
        header = tk.Label(
            self.color_frame,
            text="Chess Pilot",
            font=('Segoe UI', 18, 'bold'),
            bg=self.bg_color,
            fg=self.accent_color
        )
        header.pack(pady=(20, 10))

        color_panel = tk.Frame(self.color_frame, bg=self.frame_color, padx=20, pady=15)
        tk.Label(
            color_panel,
            text="Select Your Color:",
            font=('Segoe UI', 11),
            bg=self.frame_color,
            fg=self.text_color
        ).pack(pady=5)

        btn_frame = tk.Frame(color_panel, bg=self.frame_color)
        self.btn_white = self.create_color_button(btn_frame, "White", "w")
        self.btn_black = self.create_color_button(btn_frame, "Black", "b")
        btn_frame.pack(pady=5)

        depth_panel = tk.Frame(color_panel, bg=self.frame_color)
        tk.Label(
            depth_panel,
            text="Stockfish Depth:",
            font=('Segoe UI', 10),
            bg=self.frame_color,
            fg=self.text_color
        ).pack(anchor='w')

        self.depth_slider = ttk.Scale(
            depth_panel,
            from_=10,
            to=30,
            variable=self.depth_var,
            style="TScale",
            command=self.update_depth_label
        )
        self.depth_slider.pack(fill='x', pady=5)

        self.depth_label = tk.Label(
            depth_panel,
            text=f"Depth: {self.depth_var.get()}",
            font=('Segoe UI', 9),
            bg=self.frame_color,
            fg=self.text_color
        )
        self.depth_label.pack()

        tk.Label(
            depth_panel,
            text="\nAuto Move Screenshot Delay (sec):",
            font=('Segoe UI', 10),
            bg=self.frame_color,
            fg=self.text_color
        ).pack(anchor='w')
        self.delay_spinbox = tk.Spinbox(
            depth_panel,
            from_=0.0,
            to=1.0,
            increment=0.1,
            textvariable=self.screenshot_delay_var,
            format="%.1f",
            width=5,
            state="readonly",
            justify="center"
        )
        self.delay_spinbox.pack(anchor='w')

        depth_panel.pack(fill='x', pady=10)
        color_panel.pack(padx=30, pady=10, fill='x')
        self.color_frame.pack(expand=True, fill=tk.BOTH)

        # Main control screen (after color is chosen)
        self.main_frame = tk.Frame(self.root, bg=self.bg_color)

        control_panel = tk.Frame(self.main_frame, bg=self.frame_color, padx=20, pady=15)
        self.btn_play = self.create_action_button(
            control_panel,
            "Play Next Move",
            self.process_move_thread
        )
        self.btn_play.pack(fill='x', pady=5)

        self.castling_frame = tk.Frame(control_panel, bg=self.frame_color)
        self.kingside_var = tk.BooleanVar()
        self.queenside_var = tk.BooleanVar()
        self.create_castling_checkboxes()
        self.castling_frame.pack(pady=10)

        self.auto_mode_check = ttk.Checkbutton(
            control_panel,
            text="Auto Next Moves",
            variable=self.auto_mode_var,
            command=self.toggle_auto_mode,
            style="Castling.TCheckbutton"
        )
        self.auto_mode_check.pack(pady=5, anchor="center")

        self.status_label = tk.Label(
            control_panel,
            text="",
            font=('Segoe UI', 10),
            bg=self.frame_color,
            fg=self.text_color,
            wraplength=300
        )
        self.status_label.pack(fill='x', pady=10)

        control_panel.pack(padx=30, pady=20, fill='both', expand=True)
        self.main_frame.pack(expand=True, fill=tk.BOTH)

        # Disable "Play Next Move" until a color is chosen
        self.btn_play.config(state=tk.DISABLED)

    def update_depth_label(self, value):
        self.depth_label.config(text=f"Depth: {int(float(value))}")
        self.root.update_idletasks()

    def create_color_button(self, parent, text, color):
        btn = tk.Button(
            parent,
            text=text,
            font=('Segoe UI', 10, 'bold'),
            width=10,
            bd=0,
            padx=15,
            pady=8,
            bg=self.accent_color,
            fg=self.text_color,
            activebackground=self.hover_color,
            activeforeground=self.text_color,
            command=lambda: self.set_color(color)
        )
        btn.pack(side=tk.LEFT, padx=5)
        return btn

    def create_action_button(self, parent, text, command):
        return tk.Button(
            parent,
            text=text,
            font=('Segoe UI', 11, 'bold'),
            bg=self.accent_color,
            fg=self.text_color,
            activebackground=self.hover_color,
            activeforeground=self.text_color,
            bd=0,
            pady=10,
            command=command
        )

    def create_castling_checkboxes(self):
        style = ttk.Style()
        style.configure(
            "Castling.TCheckbutton",
            background="#373737",
            foreground="white",
            font=("Segoe UI", 10)
        )
        style.map(
            "Castling.TCheckbutton",
            background=[('active', '#333131'), ('pressed', '#333131')],
            foreground=[('active', 'white'), ('pressed', 'white')]
        )

        ttk.Checkbutton(
            self.castling_frame,
            text="Kingside Castle",
            variable=self.kingside_var,
            style="Castling.TCheckbutton"
        ).grid(row=0, column=0, padx=10, sticky='w')
        ttk.Checkbutton(
            self.castling_frame,
            text="Queenside Castle",
            variable=self.queenside_var,
            style="Castling.TCheckbutton"
        ).grid(row=1, column=0, padx=10, sticky='w')

    def update_last_fen_for_color(self, fen: str):
        """
        Split the full FEN into piece‐placement and active‐color, then store
        the placement under that active color for comparison in auto mode.
        """
        parts = fen.split()
        placement, active_color = parts[0], parts[1]
        self.last_fen_by_color[active_color] = placement

    def set_color(self, color):
        """Called when user clicks 'White' or 'Black'—switch to main controls."""
        self.color_indicator = color
        self.color_frame.pack_forget()
        self.main_frame.pack(expand=True, fill=tk.BOTH)
        self.btn_play.config(state=tk.NORMAL)
        self.update_status(f"\nPlaying as {'White' if color == 'w' else 'Black'}")

    def update_status(self, message):
        """Update the status label and refresh UI."""
        self.status_label.config(text=message)
        self.depth_label.config(text=f"Depth: {self.depth_var.get()}")
        self.root.update_idletasks()

    def process_move_thread(self):
        threading.Thread(
            target=process_move,
            args=(
                self.root,
                self.color_indicator,
                self.auto_mode_var,
                self.btn_play,
                self.board_positions,
                self.update_status,
                self.kingside_var,
                self.queenside_var,
                self.update_last_fen_for_color,
                self.last_fen_by_color,
                self.screenshot_delay_var,
                self.processing_move,
            ),
            daemon=True,
        ).start()


    def toggle_auto_mode(self):
        """
        Enable or disable auto‐move mode. When enabled, disable Play button
        and launch auto_move_loop(...) in a background thread.
        """
        if self.auto_mode_var.get():
            self.btn_play.config(state=tk.DISABLED)
            # First, play a single move to initialize if needed
            self.process_move_thread(
                self.root,
                self.color_indicator,
                self.auto_mode_var,
                self.btn_play,
                self.board_positions,
                self.update_status,
                self.kingside_var,
                self.queenside_var,
                self.update_last_fen_for_color,
                self.last_fen_by_color,
                self.screenshot_delay_var,
                self.processing_move,
            )
            # Then start continuous auto loop
            threading.Thread(
                target=auto_move_loop,
                args=(
                    self.root,
                    self.color_indicator,
                    self.auto_mode_var,
                    self.btn_play,
                    self.board_positions,
                    self.last_fen_by_color,
                    self.screenshot_delay_var,
                    self.processing_move,
                    self.update_status,
                    self.kingside_var,
                    self.queenside_var,
                    self.update_last_fen_for_color
                ),
                daemon=True
            ).start()
        else:
            self.btn_play.config(state=tk.NORMAL)

    def capture_board_screenshot(self):
        """
        Wrapper to capture a screenshot. Returns a PIL.Image or None on failure.
        """
        return capture_screenshot_in_memory(self.root, self.auto_mode_var)

    def convert_move_to_indices(self, move: str):
        """
        Wrapper to convert algebraic "e2e4" style move into (start, end) pairs.
        Returns ((c0, r0), (c1, r1)) or (None, None).
        """
        return chess_notation_to_index(
            self.color_indicator,
            self.root,
            self.auto_mode_var,
            move
        )

    def relocate_cursor_to_play_button(self):
        """
        Move the mouse cursor to the center of the Play button.
        """
        move_cursor_to_button(self.root, self.auto_mode_var, self.btn_play)

    def drag_piece(self, move: str):
        """
        Wrapper to perform GUI piece‐drag. You likely call this inside process_move().
        """
        move_piece(self.color_indicator, move, self.board_positions, self.auto_mode_var, self.root, self.btn_play)

    def expand_fen_row(self, row: str):
        """
        Wrapper for expand_fen_row(...) (if used).
        """
        return expend_fen_row(row)

    def check_castling(self, fen: str):
        """
        Wrapper to check if castling is possible.
        """
        return is_castling_possible(fen, self.color_indicator, "kingside") or \
               is_castling_possible(fen, self.color_indicator, "queenside")

    def adjust_castling_fen(self, fen: str):
        """
        Update castling rights in a FEN string based on the checkbox states.
        """
        return update_fen_castling_rights(
            self.color_indicator,
            self.kingside_var,
            self.queenside_var,
            fen
        )

    def check_move_validity(self, before_fen: str, after_fen: str, move: str):
        """
        Wrapper to verify whether a move took effect on the board.
        """
        return did_my_piece_move(self.color_indicator, before_fen, after_fen, move)

    def play_normal_move(self, move: str, mate_flag: bool, expected_fen: str):
        """
        Wrapper to execute a normal move with retries. Returns True if successful.
        """
        return execute_normal_move(
            self.board_positions,
            self.color_indicator,
            move,
            mate_flag,
            expected_fen,
            self.root,
            self.auto_mode_var,
            self.update_status,
            self.btn_play
        )

    def query_best_move(self, fen: str):
        """
        Wrapper to ask Stockfish for a best move. Returns (best_move, updated_fen, mate_flag).
        """
        return get_best_move(
            self.depth_var.get(),
            fen,
            self.root,
            self.auto_mode_var
        )

    def read_current_fen(self):
        """
        Wrapper to read the board’s FEN via screen capture and OCR.
        """
        return get_current_fen(self.color_indicator)

    def store_positions(self, x: int, y: int, size: int):
        """
        Wrapper to store board_positions after initial board cropping.
        """
        store_board_positions(self.board_positions, x, y, size)

    def verify_move_wrapper(self, before_fen: str, expected_fen: str, attempts_limit: int = 3):
        """
        Wrapper to verify move correctness with limited retries.
        """
        return verify_move(
            self.color_indicator,
            before_fen,
            expected_fen,
            attempts_limit
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = ChessPilot(root)
    root.mainloop()