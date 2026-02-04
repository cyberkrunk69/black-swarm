@echo off
setlocal enabledelayedexpansion

title Black Swarm Startup
color 0A

echo:
echo ================================================================
echo   BLACK SWARM - One-Click Startup
echo ================================================================
echo:

:: Set working directory
cd /d "%~dp0"

:: Load API key from .env if it exists
if exist ".env" (
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        if "%%a"=="GROQ_API_KEY" set GROQ_API_KEY=%%b
    )
)

:: Fallback API key if not in .env
if "%GROQ_API_KEY%"=="" (
    set GROQ_API_KEY=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
)

set INFERENCE_ENGINE=groq

echo [1/5] Checking Docker Desktop...

:: Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo       Docker not running. Starting Docker Desktop...

    :: Try common install locations
    if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
        start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    ) else if exist "%LOCALAPPDATA%\Docker\Docker Desktop.exe" (
        start "" "%LOCALAPPDATA%\Docker\Docker Desktop.exe"
    ) else (
        echo:
        echo ERROR: Docker Desktop not found!
        echo Please install Docker Desktop from https://docker.com/products/docker-desktop
        echo:
        pause
        exit /b 1
    )

    echo       Waiting for Docker to start...
    :wait_docker
    timeout /t 3 /nobreak >nul
    docker info >nul 2>&1
    if %errorlevel% neq 0 (
        echo       Still waiting...
        goto wait_docker
    )
)
echo       Docker is running.

echo:
echo [2/5] Building containers...
docker-compose build --quiet
if %errorlevel% neq 0 (
    echo ERROR: Docker build failed!
    pause
    exit /b 1
)
echo       Build complete.

echo:
echo [3/5] Starting services...
docker-compose up -d
if %errorlevel% neq 0 (
    echo ERROR: Failed to start containers!
    pause
    exit /b 1
)
echo       Services started.

echo:
echo [4/5] Waiting for dashboard to be ready...
:wait_dashboard
timeout /t 2 /nobreak >nul
curl -s http://localhost:8420 >nul 2>&1
if %errorlevel% neq 0 (
    echo       Waiting for port 8420...
    goto wait_dashboard
)
echo       Dashboard is ready.

echo:
echo [5/5] Opening browser...
start http://localhost:8420

echo:
echo ================================================================
echo   SWARM IS RUNNING
echo ================================================================
echo:
echo   Dashboard: http://localhost:8420
echo   Engine:    Groq (compound)
echo:
echo   To stop:   docker-compose down
echo   Logs:      docker-compose logs -f
echo:
echo ================================================================
echo:
echo Press any key to view live logs (Ctrl+C to exit)...
pause >nul

docker-compose logs -f
