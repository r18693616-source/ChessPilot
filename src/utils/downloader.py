#!/usr/bin/env python3
import os
import platform
import subprocess
import tarfile
import zipfile
import shutil
import tempfile
import threading
import requests
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import logging
import sys
import time

# ------------------------ Logger ------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
_ch = logging.StreamHandler(sys.stdout)
_ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(_ch)

# ------------------------ Visual style (match ChessPilot) ------------------------
BG_COLOR = "#2D2D2D"
FRAME_COLOR = "#373737"
ACCENT_COLOR = "#4CAF50"
TEXT_COLOR = "#FFFFFF"
HOVER_COLOR = "#45a049"

# ------------------------ Helpers ------------------------
def detect_os():
    p = platform.system().lower()
    if "windows" in p:
        return "windows"
    if "linux" in p:
        return "linux"
    if "darwin" in p:
        return "mac"
    return p

def detect_arch_flags():
    arch = platform.machine().lower()
    flags = set()
    os_name = detect_os()
    
    if os_name == "linux":
        try:
            # Use full path and avoid shell=True for security
            out = subprocess.check_output(["/usr/bin/lscpu"], text=True, timeout=10)
            for line in out.splitlines():
                if "Flags" in line or "flags" in line:
                    flags.update(line.split(":")[1].strip().split())
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Could not detect CPU flags on Linux: {e}")
        except Exception as e:
            logger.error(f"Unexpected error detecting CPU flags: {e}")
            
    elif os_name == "mac":
        try:
            # Use full path for security
            out = subprocess.check_output(["/usr/sbin/sysctl", "-a"], text=True, timeout=10)
            for line in out.splitlines():
                key = line.split(":")[0].strip().lower()
                if "machdep.cpu.features" in key or "machdep.cpu.leaf7_features" in key:
                    flags.update(line.split(":")[1].strip().split())
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Could not detect CPU flags on macOS: {e}")
        except Exception as e:
            logger.error(f"Unexpected error detecting CPU flags: {e}")
            
    elif os_name == "windows":
        flags.update(["sse4_1"])
        
    return arch, flags

def format_bytes(n):
    n = float(n or 0)
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"

# ------------------------ Asset selection ------------------------
def choose_best_asset(assets, os_name, arch, flags):
    filtered = []
    for a in assets:
        n = a["name"].lower()
        if os_name == "linux":
            if n.startswith("stockfish-ubuntu"):
                filtered.append(a)
        elif os_name == "mac":
            if n.startswith("stockfish-macos"):
                filtered.append(a)
        elif os_name == "windows":
            if n.startswith("stockfish-windows"):
                filtered.append(a)
                
    if not filtered:
        for a in assets:
            n = a["name"].lower()
            if os_name == "linux" and "linux" in n:
                filtered.append(a)
            elif os_name == "mac" and ("mac" in n or "darwin" in n):
                filtered.append(a)
            elif os_name == "windows" and ("win" in n or n.endswith(".zip")):
                filtered.append(a)

    if not filtered:
        return None

    score_map = {}
    for a in filtered:
        n = a["name"].lower()
        score = 0
        if "avx512" in n and any(f.startswith("avx512") for f in flags):
            score += 20
        elif "avx2" in n and "avx2" in flags:
            score += 12
        elif "bmi2" in n and "bmi2" in flags:
            score += 8
        elif "sse41" in n and ("sse4_1" in flags or "sse4_2" in flags):
            score += 6
        if n.endswith((".tar.gz", ".tgz", ".zip", ".tar")):
            score += 2
        score_map[a["name"]] = score

    best = max(score_map.items(), key=lambda kv: kv[1])[0]
    for a in filtered:
        if a["name"] == best:
            return a
    return filtered[0]

# ------------------------ Download & extraction ------------------------
def download_file(url, dest_path, progress_callback=None, chunk_size=8192, timeout=30):
    """
    Downloads a file while calling progress_callback(downloaded_bytes, total_bytes_or_None, speed_bytes_per_sec)
    """
    logger.debug(f"Starting download: {url} -> {dest_path}")
    start_time = time.time()
    downloaded = 0
    last_report_time = start_time
    last_report_bytes = 0

    try:
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            total = r.headers.get("Content-Length")
            total = int(total) if total else None
            
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        now = time.time()
                        elapsed = now - start_time if (now - start_time) > 0 else 1e-6
                        # average speed
                        speed = downloaded / elapsed
                        # report at least every 0.4s or on each chunk if small file
                        if (now - last_report_time) >= 0.4 or downloaded == total:
                            last_report_time = now
                            last_report_bytes = downloaded
                            if progress_callback:
                                try:
                                    progress_callback(downloaded, total, speed)
                                except Exception as e:
                                    logger.warning(f"Progress callback error: {e}")
                                    
    except requests.exceptions.RequestException as e:
        logger.error(f"Download failed: {e}")
        raise
    except IOError as e:
        logger.error(f"File write error: {e}")
        raise
        
    logger.debug("Download finished")

def extract_binary(archive_path):
    tmpdir = tempfile.mkdtemp()
    extracted = []
    
    try:
        if archive_path.endswith((".tar", ".tar.gz", ".tgz")):
            with tarfile.open(archive_path, "r:*") as t:
                # Security: Check for path traversal attacks
                def safe_extract(tarinfo, path):
                    if os.path.isabs(tarinfo.name) or ".." in tarinfo.name:
                        logger.warning(f"Skipping potentially dangerous path: {tarinfo.name}")
                        return None
                    return tarinfo
                
                t.extractall(tmpdir, members=[safe_extract(m, tmpdir) for m in t.getmembers() if safe_extract(m, tmpdir)])
                for root, _, files in os.walk(tmpdir):
                    for f in files:
                        extracted.append(os.path.join(root, f))
                        
        elif archive_path.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as z:
                # Security: Check for path traversal attacks
                for member in z.namelist():
                    if os.path.isabs(member) or ".." in member:
                        logger.warning(f"Skipping potentially dangerous path: {member}")
                        continue
                    z.extract(member, tmpdir)
                    
                for root, _, files in os.walk(tmpdir):
                    for f in files:
                        extracted.append(os.path.join(root, f))
        else:
            dest = os.path.join(tmpdir, os.path.basename(archive_path))
            shutil.copy2(archive_path, dest)
            extracted.append(dest)
            
    except (tarfile.TarError, zipfile.BadZipFile) as e:
        logger.error(f"Archive extraction failed: {e}")
        shutil.rmtree(tmpdir, ignore_errors=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected extraction error: {e}")
        shutil.rmtree(tmpdir, ignore_errors=True)
        return None

    for f in extracted:
        name = os.path.basename(f).lower()
        if "stockfish" in name:
            try:
                # More restrictive permissions: owner can execute, group/others can read only
                os.chmod(f, 0o744)
            except OSError as e:
                logger.warning(f"Could not set permissions on {f}: {e}")
            return f
            
    shutil.rmtree(tmpdir, ignore_errors=True)
    return None

# ------------------------ Install helpers ------------------------
def install_with_sudo(bin_path, password):
    target = "/usr/bin/stockfish"
    try:
        # Use full path to sudo for security
        cmd = ["/usr/bin/sudo", "-S", "install", "-m", "755", bin_path, target]
        proc = subprocess.run(cmd, input=(password + "\n"), text=True, 
                            capture_output=True, check=True, timeout=30)
        logger.debug("sudo install output: %s", proc.stdout)
        return True, target
    except subprocess.CalledProcessError as e:
        stderr = e.stderr or e.stdout or str(e)
        logger.error(f"sudo install failed: {stderr}")
        return False, stderr
    except subprocess.TimeoutExpired:
        logger.error("sudo install timed out")
        return False, "Installation timed out"

def install_as_root(bin_path):
    target = Path("/usr/bin/stockfish")
    try:
        shutil.copy2(bin_path, str(target))
        target.chmod(0o755)
        return True, str(target)
    except (OSError, IOError) as e:
        logger.error(f"Root install failed: {e}")
        return False, str(e)

# ------------------------ Downloader UI (styled like ChessPilot) ------------------------
class StockfishDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stockfish Downloader")
        self.root.geometry("360x140")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)

        # style
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            logger.warning("Could not set clam theme")
            
        self.style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR)
        self.style.configure("TButton", background=FRAME_COLOR, foreground=TEXT_COLOR)
        self.style.configure("TProgressbar", troughcolor=FRAME_COLOR)

        self.root.configure(bg=BG_COLOR)

        self.label = ttk.Label(root, text="Preparing...", anchor="w")
        self.label.pack(fill="x", padx=12, pady=(12, 6))

        self.progress = tk.DoubleVar(value=0.0)
        self.pb = ttk.Progressbar(root, orient="horizontal", mode="determinate", variable=self.progress, length=320)
        self.pb.pack(padx=12, pady=(0, 6))

        self.sub_label = ttk.Label(root, text="", anchor="w")
        self.sub_label.pack(fill="x", padx=12)

        # Start the operation in a daemon thread
        threading.Thread(target=self.start_download_flow, daemon=True).start()

    def set_label(self, text):
        self.root.after(0, lambda: self.label.config(text=text))
        
    def set_sub_label(self, text):
        self.root.after(0, lambda: self.sub_label.config(text=text))
        
    def set_progress(self, pct):
        self.root.after(0, lambda: self.progress.set(pct))

    def ask_sudo_password(self):
        """
        Prompt for sudo password using a styled modal (same look-and-feel as the main UI).
        Can be called from background threads: schedules modal on main thread and waits.
        Returns the password string or None if cancelled.
        """
        if threading.current_thread() is threading.main_thread():
            return self._show_password_modal()

        result = {"pw": None}
        event = threading.Event()

        def prompt():
            try:
                result["pw"] = self._show_password_modal()
            except Exception as e:
                logger.error(f"Password prompt error: {e}")
                result["pw"] = None
            finally:
                event.set()

        self.root.after(0, prompt)
        event.wait()
        return result["pw"]

    def _show_password_modal(self):
        win = tk.Toplevel(self.root)
        win.title("Administrator password")
        win.transient(self.root)
        win.grab_set()
        win.resizable(False, False)
        win.configure(bg=BG_COLOR)

        # center the modal roughly over parent
        self.root.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() // 2) - 160
        y = self.root.winfo_rooty() + (self.root.winfo_height() // 2) - 60
        win.geometry(f"320x120+{x}+{y}")

        lbl = ttk.Label(win, text="Enter your sudo password to install to /usr/bin:")
        lbl.pack(fill="x", padx=12, pady=(12, 6))

        pw_var = tk.StringVar()
        entry = ttk.Entry(win, textvariable=pw_var, show="*")
        entry.pack(fill="x", padx=12)
        entry.focus_set()

        btn_frame = tk.Frame(win, bg=BG_COLOR)
        btn_frame.pack(fill="x", pady=(10, 8))

        result = {"value": None}

        def on_ok():
            result["value"] = pw_var.get()
            win.grab_release()
            win.destroy()

        def on_cancel():
            result["value"] = None
            win.grab_release()
            win.destroy()

        ok_btn = ttk.Button(btn_frame, text="OK", command=on_ok)
        ok_btn.pack(side="right", padx=(0, 12))
        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=on_cancel)
        cancel_btn.pack(side="right", padx=(0, 6))

        # bind Enter/Escape
        win.bind('<Return>', lambda e: on_ok())
        win.bind('<Escape>', lambda e: on_cancel())

        # block until window closed
        self.root.wait_window(win)
        return result["value"]

    def close_after(self, ms=900):
        logger.debug("Window will close in %d ms", ms)
        self.root.after(ms, self.root.destroy)

    def start_download_flow(self):
        try:
            os_name = detect_os()
            arch, flags = detect_arch_flags()
            logger.info(f"Detected OS={os_name}, arch={arch}")

            if os_name == "windows":
                if getattr(sys, 'frozen', False):  # running as PyInstaller EXE
                    target_path = Path(sys.executable).parent / "stockfish.exe"
                else:
                    target_path = Path.cwd() / "stockfish.exe"
            else:
                target_path = Path("/usr/bin/stockfish")

            if target_path.exists():
                logger.info(f"Stockfish already installed at {target_path} — exiting")
                self.set_label("Already installed")
                self.set_sub_label(str(target_path))
                self.set_progress(100)
                self.close_after(800)
                return

            self.set_label("Fetching latest release metadata...")
            logger.info("Fetching latest Stockfish release metadata from GitHub")
            
            try:
                r = requests.get("https://api.github.com/repos/official-stockfish/Stockfish/releases/latest", timeout=15)
                r.raise_for_status()
                rel = r.json()
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to fetch release metadata: {e}")
                self.set_label("Network error")
                self.set_sub_label("Could not fetch release info")
                self.close_after(1200)
                return
                
            tag = rel.get("tag_name", "unknown")
            assets = [{"name": a["name"], "url": a["browser_download_url"], "size": a.get("size", 0)} 
                     for a in rel.get("assets", [])]

            best_asset = choose_best_asset(assets, os_name, arch, flags)
            if not best_asset:
                logger.error("No matching build found for this OS/arch")
                self.set_label("No matching build found")
                self.set_sub_label("See logs for details")
                self.close_after(1200)
                return

            logger.info(f"Selected asset: {best_asset['name']} (release {tag})")
            self.set_label(f"{tag} — {best_asset['name']}")
            asset_name = best_asset["name"]
            archive_path = os.path.join(tempfile.gettempdir(), asset_name)

            # check local cache
            if os.path.exists(archive_path) and best_asset.get("size"):
                try:
                    local_size = os.path.getsize(archive_path)
                    if local_size == int(best_asset.get("size", 0)):
                        logger.info("Archive already downloaded and size matches; skipping re-download")
                        self.set_sub_label("Using existing archive")
                        self.set_progress(5)
                    else:
                        logger.info("Local archive exists but size differs; re-downloading")
                except OSError as e:
                    logger.warning(f"Could not check local archive: {e}")

            # progress callback shows bytes done, total and speed
            def progress_cb(d, t, speed_bytes_per_s):
                pct = (d * 100 / t) if t else min(99.9, d / 1024 / 1024)  # if total unknown, show increasing value
                self.set_progress(pct)
                mbps = (speed_bytes_per_s * 8) / (1000 * 1000)
                speed_mb_s = speed_bytes_per_s / (1024 * 1024)
                if t:
                    self.set_sub_label(f"{format_bytes(d)} / {format_bytes(t)} — {speed_mb_s:.2f} MB/s ({mbps:.2f} Mbps)")
                else:
                    self.set_sub_label(f"{format_bytes(d)} — {speed_mb_s:.2f} MB/s ({mbps:.2f} Mbps)")

            if (not os.path.exists(archive_path)) or (best_asset.get("size") and os.path.getsize(archive_path) != int(best_asset.get("size", 0))):
                self.set_label(f"Downloading {asset_name}...")
                try:
                    download_file(best_asset["url"], archive_path, progress_callback=progress_cb)
                except Exception as e:
                    logger.error(f"Download failed: {e}")
                    self.set_label("Download failed")
                    self.set_sub_label("See logs for details")
                    self.close_after(1400)
                    return
            else:
                self.set_progress(12)

            self.set_label("Extracting binary...")
            logger.info("Extracting binary from archive")
            bin_path = extract_binary(archive_path)
            if not bin_path:
                logger.error("Could not find Stockfish binary inside the archive")
                self.set_label("Binary not found in archive")
                self.set_sub_label("See logs")
                self.close_after(1400)
                return

            self.set_progress(75)
            self.set_label("Installing...")
            if os_name == "windows":
                try:
                    shutil.copy2(bin_path, target_path)
                    logger.info("Installed Stockfish to %s", target_path)
                    self.set_label(f"Installed to {target_path.name}")
                    self.set_progress(100)
                    self.close_after(700)
                    return
                except (OSError, IOError) as e:
                    logger.error(f"Failed to copy binary on Windows: {e}")
                    self.set_label("Install failed")
                    self.set_sub_label(str(e))
                    self.close_after(1400)
                    return
            else:
                is_root = hasattr(os, "geteuid") and os.geteuid() == 0
                password = None
                if not is_root:
                    self.set_label("Administrator password required")
                    password = self.ask_sudo_password()
                    if not password:
                        logger.warning("No sudo password provided; aborting")
                        self.set_label("Aborted (no password)")
                        self.close_after(900)
                        return

                if is_root:
                    ok, info = install_as_root(bin_path)
                else:
                    ok, info = install_with_sudo(bin_path, password)

                if ok:
                    logger.info("Installed Stockfish to %s", info)
                    self.set_label(f"Installed to {Path(info).name}")
                    self.set_progress(100)
                    self.close_after(700)
                    return
                else:
                    logger.error("Install failed: %s", info)
                    self.set_label("Install failed")
                    self.set_sub_label("See logs")
                    self.close_after(1400)
                    return

        except Exception as ex:
            logger.exception("Unexpected error during download/install")
            self.set_label("Error occurred")
            self.set_sub_label(str(ex))
            self.close_after(1600)

def download_stockfish(target: Path | None = None):
    """
    Main entry point to run the Stockfish downloader app.
    Accepts optional `target` Path (e.g. Path('/usr/bin/stockfish')).
    """
    # currently the GUI installer always prompts for sudo and installs to /usr/bin (Linux)
    # Passing `target` is accepted for compatibility (resource_path passes /usr/bin).
    root = tk.Tk()
    app = StockfishDownloaderApp(root)
    root.mainloop()
    return str(target) if target else None

# ------------------------ Main ------------------------
if __name__ == "__main__":
    download_stockfish()