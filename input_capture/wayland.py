import os
import socket
import struct
import sys
from .screen_resulation import get_resolution

logging = False

# Define button constants
BUTTON_LEFT = 0x110
BUTTON_RIGHT = 0x111

def log(message):
    if logging:
        print(message)

def encode_wayland_string(s: str) -> bytes:
    if s is None:
        return struct.pack("<I", 0)
    encoded = s.encode("utf-8") + b"\x00"
    length = len(encoded)
    padding_size = (4 - (length % 4)) % 4
    padding = b"\x00" * padding_size
    return struct.pack("<I", length) + encoded + padding

class WaylandInput:
    def __init__(self):
        self.socket_path = self.get_socket_path()
        self.sock = self.connect_to_wayland()
        self.endianness = "<" if sys.byteorder == "little" else ">"
        self.wl_registry_id = 2
        self.callback_id = 3
        self.virtual_pointer_manager_id = 4
        self.next_id = 5  # Start assigning new IDs from here
        self.current_virtual_pointer_id = None

        # Perform initial setup
        self.send_registry_request()
        self.send_sync_request()
        self.handle_events()  # Binds the virtual pointer manager
        self.create_virtual_pointer()

    def get_socket_path(self):
        wayland_display = os.getenv("WAYLAND_DISPLAY", "wayland-0")
        return f"/run/user/{os.getuid()}/{wayland_display}"

    def connect_to_wayland(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.socket_path)
        log(f"Connected to Wayland server at {self.socket_path}")
        return sock

    def send_message(self, object_id, opcode, payload):
        message_size = 8 + len(payload)
        message = (
            struct.pack(f"{self.endianness}IHH", object_id, opcode, message_size)
            + payload
        )
        self.sock.sendall(message)

    def send_registry_request(self):
        self.send_message(1, 1, struct.pack(f"{self.endianness}I", self.wl_registry_id))
        log("Sent wl_display.get_registry() request...")

    def send_sync_request(self):
        self.send_message(1, 0, struct.pack(f"{self.endianness}I", self.callback_id))
        log("Sent wl_display.sync() request...")

    def receive_message(self):
        header = self.sock.recv(8)
        if len(header) < 8:
            return None, None, None
        object_id, size_opcode = struct.unpack(f"{self.endianness}II", header)
        size = (size_opcode >> 16) & 0xFFFF
        opcode = size_opcode & 0xFFFF
        message_data = self.sock.recv(size - 8)
        return object_id, opcode, message_data

    def handle_events(self):
        while True:
            object_id, opcode, message_data = self.receive_message()
            if object_id is None or opcode is None or message_data is None:
                break

            if object_id == 1:
                log(f"Received event from wl_display: {opcode}")

            if object_id == self.wl_registry_id and opcode == 0:
                global_name = struct.unpack(f"{self.endianness}I", message_data[:4])[0]
                name_offset = 4
                string_size = struct.unpack(
                    f"{self.endianness}I", message_data[name_offset : name_offset + 4]
                )[0]
                interface_name = message_data[
                    name_offset + 4 : name_offset + 4 + string_size - 1
                ].decode("utf-8")
                version = struct.unpack(f"{self.endianness}I", message_data[-4:])[0]
                log(
                    f"Discovered global: {interface_name} (name {global_name}, version {version})"
                )
                if interface_name == "zwlr_virtual_pointer_manager_v1":
                    payload = (
                        struct.pack(f"{self.endianness}I", global_name)
                        + encode_wayland_string(interface_name)
                        + struct.pack(
                            f"{self.endianness}II",
                            version,
                            self.virtual_pointer_manager_id,
                        )
                    )
                    self.send_message(self.wl_registry_id, 0, payload)
                    log("Sent zwlr_virtual_pointer_manager_v1.bind() request...")

            elif object_id == self.callback_id and opcode == 0:
                log("Received wl_callback.done event.")
                break

    def create_virtual_pointer(self):
        new_pointer_id = self.next_id
        self.next_id += 1
        self.send_message(
            self.virtual_pointer_manager_id,
            0,
            struct.pack(f"{self.endianness}II", 0, new_pointer_id),
        )
        self.current_virtual_pointer_id = new_pointer_id

    def send_motion_absolute(self, x, y, x_extent, y_extent):
        payload = struct.pack(f"{self.endianness}IIIII", 0, x, y, x_extent, y_extent)
        self.send_message(self.current_virtual_pointer_id, 1, payload)
        
    def send_click(self, button):
        # Send press then release events for the given button.
        self.send_message(self.current_virtual_pointer_id, 2, struct.pack(f"{self.endianness}III", 0, button, 1))
        self.send_message(self.current_virtual_pointer_id, 2, struct.pack(f"{self.endianness}III", 0, button, 0))

    def click(self, x, y, button=None):
        """
        Moves the pointer to (x, y) and, if button is specified, performs a click.
        """
        height, width = get_resolution()
        self.send_motion_absolute(x, y, int(height), int(width))
        
        if button is not None:
            if isinstance(button, str):
                btn = button.lower()
                if btn == "left":
                    button_code = BUTTON_LEFT
                elif btn == "right":
                    button_code = BUTTON_RIGHT
                elif btn == "nothing":
                    return
                else:
                    print("Invalid button string. Use 'left', 'right', or 'nothing'.")
                    return
            else:
                button_code = int(button)
            self.send_click(button_code)

if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python main.py <x> <y> [<button>]")
        sys.exit(1)
    
    try:
        x = int(sys.argv[1])
        y = int(sys.argv[2])
    except ValueError:
        print("x and y must be integers.")
        sys.exit(1)
    
    button = None
    if len(sys.argv) == 4:
        button_arg = sys.argv[3].lower()
        if button_arg.isdigit():
            button = int(button_arg)
        else:
            button = button_arg
    
    client = WaylandInput()
    client.click(x, y, button)