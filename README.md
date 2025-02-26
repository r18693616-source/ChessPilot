# Chess Position Evaluator

<p align="center">
  <img src="assets/chess-banner.jpg" alt="Chess Banner" width="600" />
</p>

## Features

- **Capture Chessboard**: Capture the chessboard with a single click.
- **FEN Extraction**: Extracts the FEN from the captured image using [Zai-Kun's Chess Pieces Detection](https://github.com/Zai-Kun/2d-chess-pieces-detection).
- **Automatic Board Flipping**: Automatically flips the board if you’re playing as Black.
- **Stockfish Integration**: Uses the Stockfish chess engine to suggest the best move.
- **Auto Move Execution**: Automatically plays the best move suggested by Stockfish.
- **Graphical User Interface (GUI)**: Provides a user-friendly interface instead of terminal-based interaction.
- **New Feature – ESC Key**: Allows the user to go back and select the playing color again.
- **New Feature – Castling Support**: Users can now indicate castling rights via a tick mark before each move.
- **New Feature – Depth Slider**: Users can now choose the depth for Stockfish's analysis via a slider. **Note**: More depth means longer processing time. The default depth is set to 15, which is recommended for a good balance between speed and accuracy.

---

## Download

Get the latest release from [GitHub Releases](https://github.com/OTAKUWeBer/ChessPilot/releases).

- **Linux:** [ChessPilot-linux-v2.0.0](https://github.com/OTAKUWeBer/ChessPilot/releases/download/v2.0.0/ChessPilot-linux-v2.0.0)
- **Windows:** [ChessPilot-win-v2.0.0.exe](https://github.com/OTAKUWeBer/ChessPilot/releases/download/v2.0.0/ChessPilot-win-v2.0.0.exe)

---

## Prerequisites

Ensure the following software is installed:

- **Python 3.10+**
- **Python Libraries**:
  - `requests` (`pip install requests`)
  - `mss` (`pip install mss`)
  - `Pillow` (`pip install Pillow`)
  - `pyautogui` (`pip install pyautogui`)
  - `tkinter` (usually pre-installed with Python)
- **Stockfish Chess Engine**: [Download here](https://stockfishchess.org/)

---

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/OTAKUWeBer/ChessPilot.git
   cd ChessPilot
   ```

2. **Install Python Packages:**

   ```bash
   pip install -r requirements.txt
   ```

### Linux Users

Install Stockfish via your package manager:

- **Debian/Ubuntu:**

  ```bash
  sudo apt install stockfish
  ```

- **Arch Linux:**

  ```bash
  paru/yay -S stockfish
  ```

- **Fedora:**

  ```bash
  sudo dnf install stockfish
  ```

### Windows Users

Download `stockfish.exe` from [Stockfish](https://stockfishchess.org/download/) and place it in the same directory as `main.py`.

---

## Usage

1. **Run the Script:**

   ```bash
   python main.py
   ```

2. **Choose Your Color via the GUI:**
   - Click **White** if playing as White.
   - Click **Black** if playing as Black.
   - Press **ESC** to go back and re-select your color.

3. **Indicate Castling Rights:**
   - Before each move, tick the checkbox for **Kingside Castle** or **Queenside Castle**, if applicable.

4. **Choose Depth for Move:**
   - Use the slider to select the desired depth for Stockfish's analysis. **Note**: The higher the depth, the more time it will take for Stockfish to compute the best move. The default depth is set to **15**, which is suggested for optimal performance.

5. **Tips for Best Performance:**
   - Use 100% zoom for better accuracy in chessboard detection.
   - After selecting "Play next move," the script will:
     - Extract the FEN from the image.
     - Flip the board if playing as Black.
     - Retrieve the best move from Stockfish.
     - Automatically execute the move.
   - The best move will be displayed in the GUI.
   - For improved visibility, reposition the Tkinter window so the chessboard remains clear.

---

## Disclaimer

🛑 **Use at Your Own Risk:** Using this tool in online chess games may lead to account bans.

---

## License

This project is licensed under the MIT License.

---

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests if you have suggestions or improvements.

---

## Acknowledgments

- Thanks to [Zai-Kun](https://github.com/Zai-Kun) for creating the chessboard detection model.