@echo off
setlocal EnableDelayedExpansion

REM ------------------------------------------------------------
REM Interdimensional Radio - One-Click Installer (Windows)
REM ------------------------------------------------------------
REM This script:
REM   1. Checks for Python 3.11+
REM   2. Creates a virtual environment (if missing)
REM   3. Installs Python requirements
REM   4. Downloads required model files (with progress)
REM   5. Sets up default characters
REM   6. Launches the application
REM ------------------------------------------------------------

REM ---------- Helper functions ----------
:print_error
    echo [ERROR] %~1
    exit /b 1

:print_info
    echo [INFO] %~1
    goto :eof

REM ---------- 1. Verify Python ----------
for /f "tokens=*" %%i in ('py -c "import sys; print(f\"%s.%s\" % sys.version_info[:2])" 2^>nul') do set PY_VER=%%i
if not defined PY_VER (
    call :print_error "Python not found. Install Python 3.11 or newer and ensure 'py' is in PATH."
)

for /f "tokens=1,2 delims=." %%a in ("%PY_VER%") do (
    set /a MAJOR=%%a
    set /a MINOR=%%b
)

if %MAJOR% LSS 3 (
    call :print_error "Python version %PY_VER% detected. Python 3.11+ is required."
) else if %MAJOR% EQU 3 if %MINOR% LSS 11 (
    call :print_error "Python version %PY_VER% detected. Python 3.11+ is required."
) else (
    call :print_info "Python %PY_VER% detected."
)

REM ---------- 2. Create virtual environment ----------
set VENV_DIR=venv
if not exist "%VENV_DIR%\Scripts\python.exe" (
    call :print_info "Creating virtual environment..."
    py -m venv "%VENV_DIR%" || call :print_error "Failed to create virtual environment."
) else (
    call :print_info "Virtual environment already exists."
)

REM Activate venv
call "%VENV_DIR%\Scripts\activate.bat"

REM ---------- 3. Install requirements ----------
if not exist "requirements.txt" (
    call :print_error "requirements.txt not found in the project root."
)

call :print_info "Installing Python dependencies..."
python -m pip install --upgrade pip >NUL 2>&1
python -m pip install -r requirements.txt || call :print_error "Failed to install requirements."

REM ---------- 4. Download required models ----------
REM Define model URLs and target filenames
set "MODEL_LIST=\
https://example.com/models/model_a.bin model_a.bin \
https://example.com/models/model_b.bin model_b.bin"

set "MODEL_DIR=models"
if not exist "%MODEL_DIR%" mkdir "%MODEL_DIR%"

for %%A in (%MODEL_LIST%) do (
    set "URL=%%A"
    set /a IDX+=1
    if !IDX! equ 1 set "FILENAME=%%B"
    if !IDX! equ 2 (
        set "FILENAME=%%B"
        set /a IDX=0
        if exist "%MODEL_DIR%\!FILENAME!" (
            call :print_info "Model !FILENAME! already downloaded."
        ) else (
            call :print_info "Downloading !FILENAME! ..."
            powershell -Command ^
                "$url='%URL%'; $out='%MODEL_DIR%\!FILENAME!'; ^
                $wc = New-Object System.Net.WebClient; ^
                $wc.DownloadFile($url, $out)" ^
                || call :print_error "Failed to download !FILENAME!."
        )
    )
)

REM ---------- 5. Set up default characters ----------
REM Assuming a script `setup_characters.py` exists that populates defaults.
if exist "setup_characters.py" (
    call :print_info "Setting up default characters..."
    python setup_characters.py || call :print_error "Failed to set up default characters."
) else (
    call :print_info "No character setup script found; skipping."
)

REM ---------- 6. Launch the application ----------
REM Replace `main.py` with the actual entry point if different.
if exist "main.py" (
    call :print_info "Launching Interdimensional Radio..."
    python main.py
) else (
    call :print_error "main.py not found. Cannot launch the application."
)

endlocal