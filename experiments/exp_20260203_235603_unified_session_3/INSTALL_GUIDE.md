# Interdimensional Radio – One‑Click Installer

## Overview
These installers set up **Interdimensional Radio** with a single command.  
They will:

1. Verify that **Python 3.11+** is installed.  
2. Create a virtual environment (`.venv`).  
3. Install all Python dependencies from `requirements.txt`.  
4. Download the required model files (only on the first run).  
5. Create a default character configuration.  
6. Launch the application.

After the first successful run the program works **offline** – all required files are stored locally.

---

## Windows Installation

### Prerequisites
- Python 3.11 or newer installed **and added to PATH**.  
- Internet connection for the first execution (to download models).

### Steps
1. Open **File Explorer** and navigate to the project root (`D:\codingProjects\claude_parasite_brain_suck`).
2. Double‑click `install_windows.bat`.  
   *A console window will appear; you do not need to type anything.*  
3. The script will:
   - Check Python version.
   - Create/activate a virtual environment.
   - Install packages.
   - Download model binaries to the `models` folder.
   - Create a default character file.
   - Finally start the app.

If any step fails, a clear error message will be shown in red, and the script stops.  
Fix the reported issue (e.g., install Python) and re‑run the batch file.

---

## Linux / macOS Installation

### Prerequisites
- Python 3.11+ available as `python3` on your `$PATH`.  
- `curl` (standard on most *nix) for model download.  
- Internet connection for the first execution.

### Steps
```bash
# From the project root directory:
chmod +x install_linux.sh   # make it executable (only needed once)
./install_linux.sh
```

The script will perform the same actions as the Windows version, printing progress to the terminal. Errors are displayed in red and stop execution.

---

## Offline Use
After the first successful run:

- All Python packages are stored inside `.venv`.  
- Model files live in the `models/` directory.  
- No further network access is required to start the app.

Simply run the launch command again:

- **Windows:** `.\.venv\Scripts\python -m interdimensional_radio`  
- **Linux/macOS:** `source .venv/bin/activate && python -m interdimensional_radio`

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Python not found` | Python not installed or not on PATH | Install Python 3.11+ from python.org and ensure the installer adds it to PATH. |
| `Python version 3.x.x detected` (where x < 11) | Older Python version | Install the latest Python 3.11+ and adjust PATH to point to it. |
| `Failed to create virtual environment` | Permissions or corrupted Python install | Run the installer as Administrator (Windows) or with `sudo` (Linux) or reinstall Python. |
| `pip install` errors | Missing build tools (e.g., `wheel`, `gcc`) | Install the required build tools (`build-essential` on Debian/Ubuntu, Xcode command‑line tools on macOS). |
| Model download fails | No internet or URL changed | Verify internet connectivity, or edit the URLs in the installer scripts to point to the correct model locations. |
| Application crashes on start | Incompatible dependency versions | Delete `.venv`, re‑run the installer to get a clean environment. |

---

## Customising the Installer

- **Model URLs**: Edit `install_windows.bat` (PowerShell `DownloadFile` line) or `install_linux.sh` (the `MODEL_URLS` array) to point to your own model locations.  
- **Entry point**: Replace `python -m interdimensional_radio` with the actual module or script that starts the UI if it differs.  
- **Default characters**: Adjust the JSON written under the “Set up default characters” section to suit your preferred prompts.

---

## License
The installer scripts are provided under the same license as the Interdimensional Radio project. Feel free to modify and redistribute them according to that license.

--- 

Enjoy your interdimensional conversations! 🚀