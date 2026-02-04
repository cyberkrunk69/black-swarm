@echo off
setlocal EnableDelayedExpansion

:: -------------------------------------------------
:: ONE-CLICK STARTUP SCRIPT – Windows Batch (.bat)
:: -------------------------------------------------
:: What it does:
::   1. Loads GROQ_API_KEY and INFERENCE_ENGINE from .env
::   2. Ensures Docker Desktop is running
::   3. Waits for Docker to become ready
::   4. Starts required Docker containers (docker‑compose)
::   5. Launches the swarm daemon (smart_executor)
::   6. Waits until port 8080 is listening
::   7. Opens the dashboard in the default browser
::   8. Shows live status & handles errors gracefully
:: -------------------------------------------------

echo ==================================================
echo          Starting Swarm Environment …
echo ==================================================

:: ---------- Load .env ----------
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        set "key=%%A"
        set "value=%%B"
        if /i "!key!"=="GROQ_API_KEY" set "GROQ_API_KEY=!value!"
        if /i "!key!"=="INFERENCE_ENGINE" set "INFERENCE_ENGINE=!value!"
    )
) else (
    echo [ERROR] .env file not found in %~dp0. Please create one with GROQ_API_KEY.
    pause
    exit /b 1
)

:: Ensure INFERENCE_ENGINE defaults to auto if not set
if not defined INFERENCE_ENGINE set "INFERENCE_ENGINE=auto"

:: ---------- Check Docker ----------
echo [INFO] Checking Docker status…
docker info >nul 2>&1
if errorlevel 1 (
    echo [WARN] Docker does not appear to be running.
    echo [INFO] Attempting to start Docker Desktop…
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo [INFO] Waiting for Docker to initialise (this may take a minute)…
    :waitDocker
    timeout /t 5 >nul
    docker info >nul 2>&1
    if errorlevel 1 (
        echo [INFO] Still waiting for Docker…
        goto waitDocker
    )
)

echo [INFO] Docker is up and running.

:: ---------- Start Docker containers ----------
echo [INFO] Starting required Docker containers (docker‑compose)…
docker compose up -d --remove-orphans
if errorlevel 1 (
    echo [ERROR] Failed to start Docker containers.
    pause
    exit /b 1
)

:: ---------- Launch Swarm Daemon ----------
echo [INFO] Launching swarm daemon (smart_executor)…
:: The daemon runs in its own console window so it stays alive after this script exits
start "" cmd /c "python -m smart_executor"
if errorlevel 1 (
    echo [ERROR] Failed to start the daemon process.
    pause
    exit /b 1
)

:: ---------- Wait for daemon readiness ----------
echo [INFO] Waiting for daemon to listen on port 8080…
:waitPort
timeout /t 2 >nul
netstat -ano | findstr ":8080" >nul
if errorlevel 1 (
    echo [INFO] Port 8080 not yet open – retrying…
    goto waitPort
)

echo [INFO] Daemon is ready.

:: ---------- Open Dashboard ----------
echo [INFO] Opening dashboard in default browser…
start "" "http://localhost:8080"

echo ==================================================
echo   Swarm environment started successfully!
echo   Keep this window open for live status messages.
echo   Close it when you no longer need the console.
echo ==================================================
pause