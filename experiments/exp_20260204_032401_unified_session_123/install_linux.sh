#!/usr/bin/env bash
# ==========================================================
# Interdimensional Radio - One-Click Installer (Linux / macOS)
# ==========================================================
set -euo pipefail

print_info() {
    echo -e "[INFO] $1"
}
print_error() {
    echo -e "[ERROR] $1" >&2
    exit 1
}

# ---------- 1. Verify Python ----------
if ! command -v python3 &>/dev/null; then
    print_error "Python3 is not installed or not in PATH."
fi

PY_VER=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")
MAJOR=$(echo "$PY_VER" | cut -d. -f1)
MINOR=$(echo "$PY_VER" | cut -d. -f2)

if (( MAJOR < 3 )) || { (( MAJOR == 3 )) && (( MINOR < 11 )); }; then
    print_error "Python 3.11+ is required. Detected $PY_VER."
else
    print_info "Detected Python $PY_VER."
fi

# ---------- 2. Create Virtual Environment ----------
if [ ! -d ".venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv .venv || print_error "Failed to create virtual environment."
else
    print_info "Virtual environment already exists."
fi

# ---------- 3. Activate venv ----------
source .venv/bin/activate

# ---------- 4. Upgrade pip ----------
print_info "Upgrading pip..."
pip install --upgrade pip setuptools wheel >/dev/null 2>&1 || print_error "Failed to upgrade pip."

# ---------- 5. Install requirements ----------
if [ -f "requirements.txt" ]; then
    print_info "Installing Python dependencies..."
    pip install -r requirements.txt || print_error "Failed to install dependencies."
else
    print_error "requirements.txt not found."
fi

# ---------- 6. Download required models ----------
print_info "Downloading required models..."
python - <<'EOF'
import sys, subprocess, importlib.util, os, pathlib, json, urllib.request, tqdm

def pip_install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

# Ensure tqdm is installed
if importlib.util.find_spec("tqdm") is None:
    pip_install("tqdm")

from tqdm import tqdm

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
if [ $? -ne 0 ]; then
    print_error "Model download failed."
fi

# ---------- 7. Set up default characters ----------
print_info "Setting up default characters..."
python - <<'EOF'
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
if [ $? -ne 0 ]; then
    print_error "Failed to set up default characters."
fi

# ---------- 8. Launch the application ----------
print_info "Launching Interdimensional Radio..."
python -m interdimensional_radio "$@"
if [ $? -ne 0 ]; then
    print_error "Application exited with errors."
fi