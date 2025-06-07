import logging

# Logger setup
logger = logging.getLogger(__name__)

def update_depth_label(self, value):
    logger.debug(f"Depth slider changed to {value}")
    self.depth_label.config(text=f"Depth: {int(float(value))}")
    self.root.update_idletasks()