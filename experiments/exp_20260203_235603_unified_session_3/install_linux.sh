#!/usr/bin/env bash
# --------------------------------------------------------------
# Interdimensional Radio - One-Click Installer (Linux / macOS)
# --------------------------------------------------------------
# Requirements:
#   - Python 3.11+ must be on PATH
#   - Internet connection for first run (models download)
# --------------------------------------------------------------

set -e

# Helper for error messages
error_exit() {
    echo -e "\e[31mERROR: $1\e[0m" >&2
    exit 1
}

# 1. Verify Python installation
if ! command -v python3 &>/dev/null; then
    error_exit "Python 3.11+ not found. Install it and ensure it's on your PATH."
fi

PYVER=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")
PY_MAJOR=$(python3 -c "import sys; print(sys.version_info[0])")
PY_MINOR=$(python3 -c "import sys; print(sys.version_info[1])")

if (( PY_MAJOR < 3 )) || { (( PY_MAJOR == 3 )) && (( PY_MINOR < 11 )); }; then
    error_exit "Python version $PYVER detected. Python 3.11 or newer is required."
fi

echo "Python $PYVER detected."

# 2. Create virtual environment if missing
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv || error_exit "Failed to create virtual environment."
else
    echo "Virtual environment already exists."
fi

# 3. Activate venv
source .venv/bin/activate

# 4. Upgrade pip and install requirements
echo "Upgrading pip..."
pip install --upgrade pip || error_exit "Pip upgrade failed."

if [ -f "requirements.txt" ]; then
    echo "Installing required Python packages..."
    pip install -r requirements.txt || error_exit "Failed to install dependencies."
else
    error_exit "requirements.txt not found."
fi

# 5. Download required models (only if not already present)
MODEL_DIR="models"
mkdir -p "$MODEL_DIR"

# Example model URLs – replace with real URLs as needed
MODEL_URLS=(
    "https://example.com/models/model1.bin"
    "https://example.com/models/model2.bin"
)

for URL in "${MODEL_URLS[@]}"; do
    FILENAME=$(basename "$URL")
    if [ ! -f "$MODEL_DIR/$FILENAME" ]; then
        echo "Downloading $FILENAME ..."
        # Use curl with progress bar
        curl -L --progress-bar "$URL" -o "$MODEL_DIR/$FILENAME" || error_exit "Failed to download $FILENAME."
    else
        echo "Model $FILENAME already present, skipping."
    fi
done

# 6. Set up default characters (placeholder – adjust as needed)
if [ ! -f "characters/default_character.json" ]; then
    echo "Setting up default characters..."
    mkdir -p "characters"
    cat > "characters/default_character.json" <<EOF
{
    "name": "Default",
    "prompt": "You are a helpful assistant."
}
EOF
fi

# 7. Launch the application
echo "Launching Interdimensional Radio..."
python -m interdimensional_radio  # replace with actual entry point
# If the app exits with non‑zero status, show error
if [ $? -ne 0 ]; then
    error_exit "Application failed to start."
fi