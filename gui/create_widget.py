import tkinter as tk
from tkinter import ttk
import logging
from gui.update_depth_label import update_depth_label

# Logger setup
logger = logging.getLogger(__name__)

def create_widgets(self):
    # Color selection screen
    logger.debug("Creating color selection widgets")
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

    # Depth and delay settings
    depth_panel = tk.Frame(color_panel, bg=self.frame_color)
    tk.Label(
        depth_panel,
        text="Stockfish Depth:",
        font=('Segoe UI', 10),
        bg=self.frame_color,
        fg=self.text_color
    ).pack(anchor='w')

    # Create, pack slider, then label
    self.depth_slider = ttk.Scale(
        depth_panel,
        from_=10,
        to=30,
        variable=self.depth_var,
        style="TScale",
        command=lambda val: update_depth_label(self, val)
    )
    self.depth_slider.pack(fill='x', pady=5)

    self.depth_label = tk.Label(
        depth_panel,
        text=f"Depth: {self.depth_var.get()}",
        font=('Segoe UI', 9),
        bg=self.frame_color,
        fg=self.text_color
    )
    self.depth_label.pack(pady=(0, 10))

    tk.Label(
        depth_panel,
        text="Auto Move Screenshot Delay (sec):",
        font=('Segoe UI', 10),
        bg=self.frame_color,
        fg=self.text_color
    ).pack(anchor='w')

    self.delay_spinbox = ttk.Spinbox(
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
    self.style.configure(
        "TSpinbox",
        fieldbackground="#F3F1F1",
        background=self.frame_color,
        foreground="#000000"
    )
    self.delay_spinbox.pack(anchor='w')

    depth_panel.pack(fill='x', pady=10)
    color_panel.pack(padx=30, pady=10, fill='x')
    self.color_frame.pack(expand=True, fill=tk.BOTH)

    # Main control screen (after color is chosen)
    logger.debug("Creating main control widgets")
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
    logger.debug("Widgets created successfully")
