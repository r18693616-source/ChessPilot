import tkinter as tk
from tkinter import ttk
import logging

# Logger setup
logger = logging.getLogger(__name__)

def color_button(self, parent, text, color):
    btn = tk.Button(
        parent,
        text=text,
        font=('Segoe UI', 10, 'bold'),
        width=9,
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

def action_button(self, parent, text, command):
    btn = tk.Button(
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
    btn.pack()
    return btn

def castling_checkboxes(self):
    logger.debug("Creating castling checkboxes")
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