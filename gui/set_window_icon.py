import os
import logging
from PIL import Image, ImageTk
from utils.resource_path import resource_path

# Logger setup
logger = logging.getLogger(__name__)

def set_window_icon(self):
    logo_path = resource_path(os.path.join('assets', 'chess-logo.png'))
    if os.path.exists(logo_path):
        try:
            img = Image.open(logo_path)
            self.icon = ImageTk.PhotoImage(img)
            self.root.iconphoto(False, self.icon)
            logger.debug("Window icon set successfully")
        except Exception as e:
            logger.warning(f"Failed to set window icon: {e}")