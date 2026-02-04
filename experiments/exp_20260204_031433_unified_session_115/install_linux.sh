#!/usr/bin/env bash

# ------------------------------------------------------------
# Interdimensional Radio - One-Click Installer (Linux / macOS)
# ------------------------------------------------------------
# This script:
#   1. Checks for Python 3.11+
#   2. Creates a virtual environment (if missing)
#   3. Installs Python requirements
#   4. Downloads required model files (with progress bar)
#   5. Sets up default characters
#   6. Launches the application
# ------------------------------------------------------------

set -euo pipefail

# ---------- Helper functions ----------
print_error() {
    echo -e "\e[31m[ERROR]\e[0m $1"
    exit 1
}

print_info() {
    echo -e "\e[32m[INFO]\e[0m $1"
}

# ---------- 1. Verify Python ----------
if ! command -v python3 &>/dev/null; then
    print_error "Python 3 not found. Install Python 3.11+ and ensure it's in your PATH."
fi

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)

if (( PY_MAJOR < 3 )) || { (( PY_MAJOR == 3 )) && (( PY_MINOR < 11 )); }; then
    print_error "Python version $PY_VER detected. Python 3.11+ is required."
else
    print_info "Python $PY_VER detected."
fi

# ---------- 2. Create virtual environment ----------
VENV_DIR="venv"
if [ ! -d "$VENV_DIR/bin" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv "$VENV_DIR" || print_error "Failed to create virtual environment."
else
    print_info "Virtual environment already exists."
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# ---------- 3. Install requirements ----------
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found in the project root."
fi

print_info "Installing Python dependencies..."
pip install --upgrade pip >/dev/null
pip install -r requirements.txt || print_error "Failed to install requirements."

# ---------- 4. Download required models ----------
# Define an associative array of URL -> filename
declare -A MODELS=(
    ["https://example.com/models/model_a.bin"]="model_a.bin"
    ["https://example.com/models/model_b.bin"]="model_b.bin"
)

MODEL_DIR="models"
mkdir -p "$MODEL_DIR"

for URL in "${!MODELS[@]}"; do
    FILENAME="${MODELS[$URL]}"
    TARGET_PATH="$MODEL_DIR/$FILENAME"
    if [ -f "$TARGET_PATH" ]; then
        print_info "Model $FILENAME already downloaded."
        continue
    fi
    print_info "Downloading $FILENAME ..."
    # Use curl with a progress bar
    curl -L "$URL" -o "$TARGET_PATH" --progress-bar || {
        print_error "Failed to download $FILENAME."
    }
done

# ---------- 5. Set up default characters ----------
if [ -f "setup_characters.py" ]; then
    print_info "Setting up default characters..."
    python setup_characters.py || print_error "Failed to set up default characters."
else
    print_info "No character setup script found; skipping."
fi

# ---------- 6. Launch the application ----------
# Replace `main.py` with the actual entry point if different.
if [ -f "main.py" ]; then
    print_info "Launching Interdimensional Radio..."
    python main.py
else
    print_error "main.py not found. Cannot launch the application."
fi