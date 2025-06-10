# Chess Position Evaluator

<p align="center">
  <img src="assets/chess-banner.jpg" alt="Chess Banner" width="600" />
</p>

## Features

- **FEN Extraction**: Detects the board position from your screen using [Zai-Kun’s Chess Pieces Detection](https://github.com/Zai-Kun/2d-chess-pieces-detection).  
- **Local Model Inference**: Runs a local ONNX model for fast, offline board recognition.  
- **Stockfish Integration**: Uses the Stockfish engine to analyze the position and suggest the best move.  
- **Auto Move Execution**: Automatically plays the recommended move on your screen.  
- **Manual Play**: Click the **“Play Next Move”** button whenever you’re ready.  
- **Board Flipping**: Automatically flips the board if you choose to play Black.  
- **Castling Support**: Check “Kingside” or “Queenside” to enable castling rights.  
- **Depth Control**: Adjust Stockfish’s analysis depth with a slider (default: 15).  
- **Retry Mechanism**: Retries a failed move up to three times.  
- **ESC Key**: Press **ESC** to reselect your color at any time.  
- **GUI Interface**: Built with Tkinter for a simple, interactive experience.  
- **Fully Offline**: All processing happens locally—no external API calls.

---

## Download

Grab the latest release from our [GitHub Releases page](https://github.com/OTAKUWeBer/ChessPilot/releases/latest/).

### Required Files

1. **ONNX Chess Detection Model**  
   Download from:  
   [chess_detectionv0.0.4.onnx](https://github.com/Zai-Kun/2d-chess-pieces-detection/releases/download/v0.0.4/chess_detectionv0.0.4.onnx)  
   > **Note:** On Windows you may need the Microsoft Visual C++ Redistributable.  
   > Get it here: [Microsoft VC++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170)

2. **Stockfish Engine**  
   Download a ZIP from:  
   [Stockfish Downloads](https://stockfishchess.org/download/)  

> **Important:** Place both the ONNX model and the Stockfish ZIP (or extracted binary) either in the **project root** next to `src/` or directly inside `src/`. The program will detect them automatically.

---

## Prerequisites

- **Python 3.10+**
- Install dependencies:

```bash
  pip install -r requirements.txt
```

* If `tkinter` is not installed:

  * **Ubuntu / Debian**

    ```bash
    sudo apt install python3-tk
    ```
  * **Arch Linux**

    ```bash
    sudo pacman -S tk
    ```
  * **Fedora**

    ```bash
    sudo dnf install python3-tkinter
    ```

---

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/OTAKUWeBer/ChessPilot.git
   cd ChessPilot
   ```

2. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Add required files**

   Ensure the ONNX model (`chess_detectionv0.0.4.onnx`) and the Stockfish ZIP or binary are placed either in the **project root** (alongside `src/`) or inside the `src/` directory.

---

## Usage

From the project root, run:

```bash
python src/main.py
```

Alternatively, you can:

```bash
cd src
python main.py
```

1. **Select your color** (White or Black)
2. **Enable castling** (check “Kingside” or “Queenside” if applicable)
3. **Adjust analysis depth** (slider, default 15)
4. **Choose play mode**

   * *Manual*: Click **“Play Next Move”** for each move.
   * *Auto*: Enable automatic play of recommended moves.
5. The tool will **retry** any failed move up to three times.

---

## Platform Notes

### Linux

Install Stockfish via your package manager:

```bash
# Ubuntu / Debian
sudo apt install stockfish

# Arch Linux
paru -S stockfish

# Fedora
sudo dnf install stockfish
```

#### Wayland (Hyprland, Sway)

Install screenshot utilities:

```bash
sudo pacman -S grim wayland-utils
```

---

## Shortcuts

See [SHORTCUTS.md](SHORTCUTS.md) for a complete list of keyboard shortcuts.

---

## Tips for Best Results

   * Use **100% zoom** in your browser or chess interface.
   * Keep the Tkinter window out of the way of the board.
   * Keep your board square and aligned.

---

## Disclaimer

🛑 **Use at Your Own Risk**: Automating chess play may violate terms of service on online platforms. You are responsible for how you use this tool.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests if you have suggestions or improvements.

---

## Acknowledgments

* Thanks to [Zai-Kun](https://github.com/Zai-Kun) for the ONNX chessboard detection model and Wayland support.