import tkinter as tk
import logging

# Logger setup
logger = logging.getLogger(__name__)

def handle_esc_key(self, event=None):
    self.root.bind('<Escape>', handle_esc_key(self))
    """Return to color‐selection screen if ESC is pressed."""
    logger.info("ESC key pressed; returning to color selection")
    if self.main_frame.winfo_ismapped():
        self.main_frame.pack_forget()
        self.color_frame.pack(expand=True, fill=tk.BOTH)
        self.color_indicator = None
        self.btn_play.config(state=tk.DISABLED)
        self.update_status("")
        self.auto_mode_var.set(False)
        self.btn_play.config(state=tk.NORMAL)
        
def bind_shortcuts(self):
    """Bind keyboard shortcuts to various actions."""
    # Color selection shortcuts (always allowed)
    self.root.bind('<Key-w>', lambda e: self.set_color('w'))
    self.root.bind('<Key-b>', lambda e: self.set_color('b'))
    # Main control shortcuts (only if color_indicator is set)
    self.root.bind(
        '<Key-p>',
        lambda e: self.process_move_thread() if self.color_indicator else None
    )
    self.root.bind(
        '<Key-a>',
        lambda e: self.auto_mode_check.invoke() if self.color_indicator else None
    )
    self.root.bind(
        '<Key-k>',
        lambda e: self.kingside_var.set(not self.kingside_var.get()) if self.color_indicator else None)
    self.root.bind(
        '<Key-q>',
        lambda e: self.queenside_var.set(not self.queenside_var.get()) if self.color_indicator else None)

    # Screenshot delay adjustment with Up/Down arrows
    self.root.bind(
        '<Up>',
        lambda e: (
            self.screenshot_delay_var.set(
                round(min(1.0, self.screenshot_delay_var.get() + 0.1), 1)
            ),
        ) if self.color_indicator is None else None
    )
    
    self.root.bind(
        '<Down>',
        lambda e: (
            self.screenshot_delay_var.set(
                round(max(0.0, self.screenshot_delay_var.get() - 0.1), 1)
            ),
        ) if self.color_indicator is None else None
    )

    # Depth adjustment with Right/Left arrows
    self.root.bind(
        '<Right>',
        lambda e: (
            self.depth_var.set(min(30, self.depth_var.get() + 1)),
            self.update_status(f"Depth: {self.depth_var.get()}")
        ) if self.color_indicator is None else None
    )
    self.root.bind(
        '<Left>',
        lambda e: (
            self.depth_var.set(max(1, self.depth_var.get() - 1)),
            self.update_status(f"Depth: {self.depth_var.get()}")
        ) if self.color_indicator is None else None
    )
