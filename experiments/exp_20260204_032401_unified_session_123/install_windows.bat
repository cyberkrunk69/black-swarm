@echo off
REM ==========================================================
REM Interdimensional Radio - One-Click Installer (Windows)
REM ==========================================================
setlocal EnableDelayedExpansion

REM ---------- Helper Functions ----------
:print_error
echo [ERROR] %~1
exit /b 1

:print_info
echo [INFO] %~1
goto :eof

REM ---------- 1. Verify Python ----------
for /f "tokens=* usebackq" %%i in (`python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2^>nul`) do set PY_VER=%%i
if not defined PY_VER (
    call :print_error "Python is not installed or not added to PATH."
)

for /f "delims=." %%a in ("%PY_VER%") do set MAJOR=%%a
for /f "delims=." %%b in ("%PY_VER%") do set MINOR=%%b

if %MAJOR% LSS 3 (
    call :print_error "Python 3 is required."
) else if %MAJOR% EQU 3 if %MINOR% LSS 11 (
    call :print_error "Python 3.11 or newer is required. Detected %PY_VER%."
) else (
    call :print_info "Detected Python %PY_VER%."
)

REM ---------- 2. Create Virtual Environment ----------
if not exist ".venv" (
    call :print_info "Creating virtual environment..."
    python -m venv .venv || call :print_error "Failed to create virtual environment."
) else (
    call :print_info "Virtual environment already exists."
)

REM ---------- 3. Activate venv ----------
call .venv\Scripts\activate.bat

REM ---------- 4. Upgrade pip ----------
call :print_info "Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel >nul 2>&1 || call :print_error "Failed to upgrade pip."

REM ---------- 5. Install requirements ----------
if exist "requirements.txt" (
    call :print_info "Installing Python dependencies..."
    pip install -r requirements.txt || call :print_error "Failed to install dependencies."
) else (
    call :print_error "requirements.txt not found."
)

REM ---------- 6. Download required models ----------
REM The download script uses tqdm for a progress bar.
call :print_info "Downloading required models..."
python - <<EOF
import sys, subprocess, importlib.util, os, pathlib, json, urllib.request, tqdm

def pip_install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

# Ensure tqdm is available
if importlib.util.find_spec("tqdm") is None:
    pip_install("tqdm")

from tqdm import tqdm

# Define models (URL -> target path)
models = {
    "https://example.com/models/model_a.bin": "models/model_a.bin",
    "https://example.com/models/model_b.bin": "models/model_b.bin"
}

os.makedirs("models", exist_ok=True)

def download(url, dest):
    dest_path = pathlib.Path(dest)
    if dest_path.is_file():
        print(f"{dest} already exists, skipping.")
        return
    with urllib.request.urlopen(url) as resp, open(dest, "wb") as out_file:
        total = int(resp.getheader("Content-Length", 0))
        with tqdm.tqdm(total=total, unit="B", unit_scale=True, desc=dest_path.name) as pbar:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                out_file.write(chunk)
                pbar.update(len(chunk))

for url, path in models.items():
    try:
        download(url, path)
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        sys.exit(1)
EOF
if errorlevel 1 (
    call :print_error "Model download failed."
)

REM ---------- 7. Set up default characters ----------
call :print_info "Setting up default characters..."
python - <<EOF
import os, json, pathlib

characters_dir = pathlib.Path("characters")
characters_dir.mkdir(exist_ok=True)

default_character = {
    "name": "Chronos",
    "description": "A friendly interdimensional guide.",
    "voice": "default"
}

default_path = characters_dir / "chronos.json"
if not default_path.is_file():
    with open(default_path, "w", encoding="utf-8") as f:
        json.dump(default_character, f, indent=2)
    print("Default character created.")
else:
    print("Default character already exists.")
EOF
if errorlevel 1 (
    call :print_error "Failed to set up default characters."
)

REM ---------- 8. Launch the application ----------
call :print_info "Launching Interdimensional Radio..."
python -m interdimensional_radio %*
if errorlevel 1 (
    call :print_error "Application exited with errors."
)

endlocal