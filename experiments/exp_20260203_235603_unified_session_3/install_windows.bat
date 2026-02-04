@echo off
setlocal EnableDelayedExpansion

:: --------------------------------------------------------------
:: Interdimensional Radio - One-Click Installer (Windows)
:: --------------------------------------------------------------
:: Requirements:
::   - Python 3.11 or newer must be on PATH
::   - Internet connection for first run (models download)
:: --------------------------------------------------------------

:: Helper function to print errors in red
:print_error
    echo.
    echo %~1
    exit /b 1

:: 1. Verify Python installation
where python >nul 2>&1
if errorlevel 1 (
    call :print_error "ERROR: Python not found in PATH. Please install Python 3.11+ and add it to your system PATH."
)

:: Get Python version
for /f "tokens=2 delims= " %%A in ('python -c "import sys; print(sys.version)"') do set PYVER=%%A
for /f "tokens=1 delims=." %%A in ("%PYVER%") do set PY_MAJOR=%%A
for /f "tokens=2 delims=." %%A in ("%PYVER%") do set PY_MINOR=%%A

if %PY_MAJOR% LSS 3 (
    call :print_error "ERROR: Python version %PYVER% detected. Python 3.11 or newer is required."
) else if %PY_MAJOR% EQU 3 if %PY_MINOR% LSS 11 (
    call :print_error "ERROR: Python version %PYVER% detected. Python 3.11 or newer is required."
)

echo Python %PYVER% detected.

:: 2. Create virtual environment if it doesn't exist
if not exist ".venv\" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        call :print_error "ERROR: Failed to create virtual environment."
    )
) else (
    echo Virtual environment already exists.
)

:: 3. Activate venv
call .venv\Scripts\activate.bat
if errorlevel 1 (
    call :print_error "ERROR: Failed to activate virtual environment."
)

:: 4. Upgrade pip and install requirements
echo Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    call :print_error "ERROR: Pip upgrade failed."
)

if exist "requirements.txt" (
    echo Installing required Python packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        call :print_error "ERROR: Failed to install Python dependencies."
    )
) else (
    call :print_error "ERROR: requirements.txt not found in the project root."
)

:: 5. Download required models (only if not already present)
set "MODEL_DIR=models"
if not exist "%MODEL_DIR%" (
    mkdir "%MODEL_DIR%"
)

:: Example model URLs – replace with real URLs as needed
set "MODEL_URLS=https://example.com/models/model1.bin https://example.com/models/model2.bin"

for %%U in (%MODEL_URLS%) do (
    for %%F in (%%U) do set "FILENAME=%%~nxF"
    if not exist "%MODEL_DIR%\!FILENAME!" (
        echo Downloading !FILENAME! ...
        powershell -Command ^
            "$url='%%U'; $out='%MODEL_DIR%\!FILENAME!'; ^
            $wc = New-Object System.Net.WebClient; ^
            $wc.DownloadFile($url, $out)"
        if errorlevel 1 (
            call :print_error "ERROR: Failed to download !FILENAME!."
        )
    ) else (
        echo Model !FILENAME! already present, skipping.
    )
)

:: 6. Set up default characters (placeholder – adjust as needed)
if not exist "characters\default_character.json" (
    echo Setting up default characters...
    mkdir "characters" >nul 2>&1
    echo {\"name\": \"Default\", \"prompt\": \"You are a helpful assistant.\"} > "characters\default_character.json"
)

:: 7. Launch the application
echo Launching Interdimensional Radio...
python -m interdimensional_radio  :: replace with actual entry point
if errorlevel 1 (
    call :print_error "ERROR: Application failed to start."
)

endlocal