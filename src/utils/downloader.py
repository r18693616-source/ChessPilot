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
        flags = _detect_linux_cpu_flags()
    elif os_name == "mac":
        flags = _detect_mac_cpu_flags()
    elif os_name == "windows":
        flags.update(["sse4_1"])
        
    return arch, flags

def _detect_linux_cpu_flags():
    flags = set()
    try:
        out = subprocess.check_output(["/usr/bin/lscpu"], text=True, timeout=10)
        for line in out.splitlines():
            if "Flags" in line or "flags" in line:
                flags.update(line.split(":")[1].strip().split())
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning(f"Could not detect CPU flags on Linux: {e}")
    except Exception as e:
        logger.error(f"Unexpected error detecting CPU flags: {e}")
    return flags

def _detect_mac_cpu_flags():
    flags = set()
    try:
        out = subprocess.check_output(["/usr/sbin/sysctl", "-a"], text=True, timeout=10)
        for line in out.splitlines():
            key = line.split(":")[0].strip().lower()
            if "machdep.cpu.features" in key or "machdep.cpu.leaf7_features" in key:
                flags.update(line.split(":")[1].strip().split())
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning(f"Could not detect CPU flags on macOS: {e}")
    except Exception as e:
        logger.error(f"Unexpected error detecting CPU flags: {e}")
    return flags

def format_bytes(n):
    n = float(n or 0)
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"

# ------------------------ Asset selection ------------------------
def choose_best_asset(assets, os_name, arch, flags):
    filtered = _filter_assets_by_os(assets, os_name)
    if not filtered:
        return None
    
    return _select_best_by_cpu_features(filtered, flags)

def _filter_assets_by_os(assets, os_name):
    filtered = []
    
    # First pass: Look for OS-specific prefixes
    for a in assets:
        n = a["name"].lower()
        if _matches_os_prefix(n, os_name):
            filtered.append(a)
    
    # Second pass: Fallback to generic OS indicators
    if not filtered:
        for a in assets:
            n = a["name"].lower()
            if _matches_os_generic(n, os_name):
                filtered.append(a)
    
    return filtered

def _matches_os_prefix(name, os_name):
    if os_name == "linux" and name.startswith("stockfish-ubuntu"):
        return True
    if os_name == "mac" and name.startswith("stockfish-macos"):
        return True
    if os_name == "windows" and name.startswith("stockfish-windows"):
        return True
    return False

def _matches_os_generic(name, os_name):
    if os_name == "linux" and "linux" in name:
        return True
    if os_name == "mac" and ("mac" in name or "darwin" in name):
        return True
    if os_name == "windows" and ("win" in name or name.endswith(".zip")):
        return True
    return False

def _select_best_by_cpu_features(filtered, flags):
    score_map = {}
    for a in filtered:
        score = _calculate_cpu_score(a["name"].lower(), flags)
        score_map[a["name"]] = score

    best = max(score_map.items(), key=lambda kv: kv[1])[0]
    for a in filtered:
        if a["name"] == best:
            return a
    return filtered[0]

def _calculate_cpu_score(name, flags):
    score = 0
    if "avx512" in name and any(f.startswith("avx512") for f in flags):
        score += 20
    elif "avx2" in name and "avx2" in flags:
        score += 12
    elif "bmi2" in name and "bmi2" in flags:
        score += 8
    elif "sse41" in name and ("sse4_1" in flags or "sse4_2" in flags):
        score += 6
    if name.endswith((".tar.gz", ".tgz", ".zip", ".tar")):
        score += 2
    return score

# ------------------------ Download & extraction ------------------------
def download_file(url, dest_path, progress_callback=None, chunk_size=8192, timeout=30):
    """
    Downloads a file while calling progress_callback(downloaded_bytes, total_bytes_or_None, speed_bytes_per_sec)
    """
    logger.debug(f"Starting download: {url} -> {dest_path}")
    start_time = time.time()
    downloaded = 0
    last_report_time = start_time

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
                        speed = downloaded / elapsed
                        
                        if (now - last_report_time) >= 0.4 or downloaded == total:
                            last_report_time = now
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

class BinaryExtractor:
    def __init__(self, archive_path):
        self.archive_path = archive_path
        self.tmpdir = None
        
    def extract_binary(self):
        self.tmpdir = tempfile.mkdtemp()
        extracted = []
        
        try:
            if self._is_tar_archive():
                extracted = self._extract_tar()
            elif self._is_zip_archive():
                extracted = self._extract_zip()
            else:
                extracted = self._copy_single_file()
                
        except (tarfile.TarError, zipfile.BadZipFile) as e:
            logger.error(f"Archive extraction failed: {e}")
            self._cleanup()
            return None
        except Exception as e:
            logger.error(f"Unexpected extraction error: {e}")
            self._cleanup()
            return None

        binary_path = self._find_stockfish_binary(extracted)
        if binary_path:
            self._set_binary_permissions(binary_path)
        else:
            self._cleanup()
        
        return binary_path
    
    def _is_tar_archive(self):
        return self.archive_path.endswith((".tar", ".tar.gz", ".tgz"))
    
    def _is_zip_archive(self):
        return self.archive_path.endswith(".zip")
    
    def _extract_tar(self):
        extracted = []
        with tarfile.open(self.archive_path, "r:*") as t:
            for member in t.getmembers():
                if self._is_safe_path(member.name):
                    t.extract(member, self.tmpdir)
                    
            for root, _, files in os.walk(self.tmpdir):
                for f in files:
                    extracted.append(os.path.join(root, f))
        return extracted
    
    def _extract_zip(self):
        extracted = []
        with zipfile.ZipFile(self.archive_path, "r") as z:
            for member in z.namelist():
                if self._is_safe_path(member):
                    z.extract(member, self.tmpdir)
                    
            for root, _, files in os.walk(self.tmpdir):
                for f in files:
                    extracted.append(os.path.join(root, f))
        return extracted
    
    def _copy_single_file(self):
        dest = os.path.join(self.tmpdir, os.path.basename(self.archive_path))
        shutil.copy2(self.archive_path, dest)
        return [dest]
    
    def _is_safe_path(self, path):
        if os.path.isabs(path) or ".." in path:
            logger.warning(f"Skipping potentially dangerous path: {path}")
            return False
        return True
    
    def _find_stockfish_binary(self, extracted):
        for f in extracted:
            name = os.path.basename(f).lower()
            if "stockfish" in name:
                return f
        return None
    
    def _set_binary_permissions(self, binary_path):
        try:
            os.chmod(binary_path, 0o744)
        except OSError as e:
            logger.warning(f"Could not set permissions on {binary_path}: {e}")
    
    def _cleanup(self):
        if self.tmpdir:
            shutil.rmtree(self.tmpdir, ignore_errors=True)

def extract_binary(archive_path):
    extractor = BinaryExtractor(archive_path)
    return extractor.extract_binary()

# ------------------------ Install helpers ------------------------
def install_with_sudo(bin_path, password):
    target = "/usr/bin/stockfish"
    try:
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

# NOTE: Above helpers are kept for compatibility but will not be used in the simplified flow.

# ------------------------ Download workflow ------------------------
class DownloadWorkflow:
    def __init__(self, ui_callbacks):
        self.ui = ui_callbacks
        self.os_name = detect_os()
        self.arch, self.flags = detect_arch_flags()
        
    def execute(self):
        try:
            logger.info(f"Detected OS={self.os_name}, arch={self.arch}")
            
            if self._is_already_installed():
                return
                
            release_data = self._fetch_release_data()
            if not release_data:
                return
                
            best_asset = self._select_asset(release_data)
            if not best_asset:
                return
                
            archive_path = self._download_asset(best_asset, release_data["tag_name"])
            if not archive_path:
                return
                
            binary_path = self._extract_binary(archive_path)
            if not binary_path:
                return
                
            self._install_binary(binary_path)
            
        except Exception as ex:
            logger.exception("Unexpected error during download/install")
            self.ui.set_label("Error occurred")
            self.ui.set_sub_label(str(ex))
            self.ui.close_after(1600)
    
    def _is_already_installed(self):
        target_path = self._get_target_path()
        if target_path.exists():
            logger.info(f"Stockfish already installed at {target_path} — exiting")
            self.ui.set_label("Already installed")
            self.ui.set_sub_label(str(target_path))
            self.ui.set_progress(100)
            self.ui.close_after(800)
            return True
        return False
    
    def _get_target_path(self):
        # Minimal behavior: install next to executable (if frozen) or to current working directory
        if self.os_name == "windows":
            if getattr(sys, 'frozen', False):
                return Path(sys.executable).parent / "stockfish.exe"
            else:
                return Path.cwd() / "stockfish.exe"
        else:
            if getattr(sys, 'frozen', False):
                return Path(sys.executable).parent / "stockfish"
            else:
                return Path.cwd() / "stockfish"
    
    def _fetch_release_data(self):
        self.ui.set_label("Fetching latest release metadata...")
        logger.info("Fetching latest Stockfish release metadata from GitHub")
        
        try:
            r = requests.get("https://api.github.com/repos/official-stockfish/Stockfish/releases/latest", timeout=15)
            r.raise_for_status()
            rel = r.json()
            
            tag = rel.get("tag_name", "unknown")
            assets = [{"name": a["name"], "url": a["browser_download_url"], "size": a.get("size", 0)} 
                     for a in rel.get("assets", [])]
            
            return {"tag_name": tag, "assets": assets}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch release metadata: {e}")
            self.ui.set_label("Network error")
            self.ui.set_sub_label("Could not fetch release info")
            self.ui.close_after(1200)
            return None
    
    def _select_asset(self, release_data):
        best_asset = choose_best_asset(release_data["assets"], self.os_name, self.arch, self.flags)
        if not best_asset:
            logger.error("No matching build found for this OS/arch")
            self.ui.set_label("No matching build found")
            self.ui.set_sub_label("See logs for details")
            self.ui.close_after(1200)
            return None
            
        logger.info(f"Selected asset: {best_asset['name']} (release {release_data['tag_name']})")
        return best_asset
    
    def _download_asset(self, best_asset, tag_name):
        self.ui.set_label(f"{tag_name} — {best_asset['name']}")
        asset_name = best_asset["name"]
        archive_path = os.path.join(tempfile.gettempdir(), asset_name)

        if self._is_cached_and_valid(archive_path, best_asset):
            self.ui.set_sub_label("Using existing archive")
            self.ui.set_progress(5)
            return archive_path

        self.ui.set_label(f"Downloading {asset_name}...")
        try:
            download_file(best_asset["url"], archive_path, progress_callback=self._create_progress_callback())
            return archive_path
        except Exception as e:
            logger.error(f"Download failed: {e}")
            self.ui.set_label("Download failed")
            self.ui.set_sub_label("See logs for details")
            self.ui.close_after(1400)
            return None
    
    def _is_cached_and_valid(self, archive_path, asset):
        if not os.path.exists(archive_path):
            return False
            
        if not asset.get("size"):
            return True
            
        try:
            local_size = os.path.getsize(archive_path)
            if local_size == int(asset.get("size", 0)):
                logger.info("Archive already downloaded and size matches; skipping re-download")
                return True
            else:
                logger.info("Local archive exists but size differs; re-downloading")
                return False
        except OSError as e:
            logger.warning(f"Could not check local archive: {e}")
            return False
    
    def _create_progress_callback(self):
        def progress_cb(d, t, speed_bytes_per_s):
            pct = (d * 100 / t) if t else min(99.9, d / 1024 / 1024)
            self.ui.set_progress(pct)
            mbps = (speed_bytes_per_s * 8) / (1000 * 1000)
            speed_mb_s = speed_bytes_per_s / (1024 * 1024)
            if t:
                self.ui.set_sub_label(f"{format_bytes(d)} / {format_bytes(t)} — {speed_mb_s:.2f} MB/s ({mbps:.2f} Mbps)")
            else:
                self.ui.set_sub_label(f"{format_bytes(d)} — {speed_mb_s:.2f} MB/s ({mbps:.2f} Mbps)")
        return progress_cb
    
    def _extract_binary(self, archive_path):
        self.ui.set_label("Extracting binary...")
        logger.info("Extracting binary from archive")
        bin_path = extract_binary(archive_path)
        if not bin_path:
            logger.error("Could not find Stockfish binary inside the archive")
            self.ui.set_label("Binary not found in archive")
            self.ui.set_sub_label("See logs")
            self.ui.close_after(1400)
            return None
        
        self.ui.set_progress(75)
        return bin_path
    
    def _install_binary(self, bin_path):
        self.ui.set_label("Installing...")
        target_path = self._get_target_path()
        
        if self.os_name == "windows":
            self._install_windows(bin_path, target_path)
        else:
            # simplified: install into current working directory / executable dir like Windows
            self._install_unix(bin_path, target_path)
    
    def _install_windows(self, bin_path, target_path):
        try:
            shutil.copy2(bin_path, target_path)
            logger.info("Installed Stockfish to %s", target_path)
            self.ui.set_label(f"Installed to {target_path.name}")
            self.ui.set_progress(100)
            self.ui.close_after(700)
        except (OSError, IOError) as e:
            logger.error(f"Failed to copy binary on Windows: {e}")
            self.ui.set_label("Install failed")
            self.ui.set_sub_label(str(e))
            self.ui.close_after(1400)
    
    def _install_unix(self, bin_path, target_path):
        try:
            shutil.copy2(bin_path, target_path)
            os.chmod(target_path, 0o700)
            logger.info("Installed Stockfish to %s", target_path)
            self.ui.set_label(f"Installed to {target_path.name}")
            self.ui.set_progress(100)
            self.ui.close_after(700)
        except (OSError, IOError) as e:
            logger.error(f"Failed to copy binary on Unix-like OS: {e}")
            self.ui.set_label("Install failed")
            self.ui.set_sub_label(str(e))
            self.ui.close_after(1400)

# ------------------------ Downloader UI (styled like ChessPilot) ------------------------
class StockfishDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stockfish Downloader")
        self.root.geometry("360x140")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)

        self._setup_styles()
        self._create_widgets()
        
        # Start the operation in a daemon thread
        threading.Thread(target=self._start_download_flow, daemon=True).start()

    def _setup_styles(self):
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            logger.warning("Could not set clam theme")
            
        self.style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR)
        self.style.configure("TButton", background=FRAME_COLOR, foreground=TEXT_COLOR)
        self.style.configure("TProgressbar", troughcolor=FRAME_COLOR)
        self.root.configure(bg=BG_COLOR)
    
    def _create_widgets(self):
        self.label = ttk.Label(self.root, text="Preparing...", anchor="w")
        self.label.pack(fill="x", padx=12, pady=(12, 6))

        self.progress = tk.DoubleVar(value=0.0)
        self.pb = ttk.Progressbar(self.root, orient="horizontal", mode="determinate", 
                                 variable=self.progress, length=320)
        self.pb.pack(padx=12, pady=(0, 6))

        self.sub_label = ttk.Label(self.root, text="", anchor="w")
        self.sub_label.pack(fill="x", padx=12)

    def set_label(self, text):
        self.root.after(0, lambda: self.label.config(text=text))
        
    def set_sub_label(self, text):
        self.root.after(0, lambda: self.sub_label.config(text=text))
        
    def set_progress(self, pct):
        self.root.after(0, lambda: self.progress.set(pct))

    def close_after(self, ms=900):
        logger.debug("Window will close in %d ms", ms)
        self.root.after(ms, self.root.destroy)

    def _start_download_flow(self):
        workflow = DownloadWorkflow(self)
        workflow.execute()

def download_stockfish(target: Path | None = None):
    """
    Main entry point to run the Stockfish downloader app.
    Accepts optional `target` Path (e.g. Path('/usr/bin/stockfish')).
    """
    # GUI installer now installs into working directory / executable dir (no sudo)
    root = tk.Tk()
    app = StockfishDownloaderApp(root)
    root.mainloop()
    return str(target) if target else None

# ------------------------ Main ------------------------
if __name__ == "__main__":
    download_stockfish()
