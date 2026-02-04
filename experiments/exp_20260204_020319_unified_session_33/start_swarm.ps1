<#
.SYNOPSIS
    ONE-CLICK STARTUP SCRIPT – PowerShell version for Windows Terminal users.
.DESCRIPTION
    Performs the same steps as start_swarm.bat but uses native PowerShell commands.
    - Loads GROQ_API_KEY & INFERENCE_ENGINE from .env
    - Starts Docker Desktop if needed
    - Waits for Docker to be ready
    - Brings up docker‑compose services
    - Starts the swarm daemon (smart_executor)
    - Waits for port 8080 to listen
    - Opens the dashboard in the default browser
    - Shows live status & handles errors gracefully
#>

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "          Starting Swarm Environment (PowerShell)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# ---------- Load .env ----------
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#\s][^=]*)\s*=\s*(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            switch ($name) {
                'GROQ_API_KEY' { $env:GROQ_API_KEY = $value }
                'INFERENCE_ENGINE' { $env:INFERENCE_ENGINE = $value }
            }
        }
    }
} else {
    Write-Error ".env file not found in $PSScriptRoot. Please create one with GROQ_API_KEY."
    exit 1
}

if (-not $env:INFERENCE_ENGINE) { $env:INFERENCE_ENGINE = "auto" }

# ---------- Check Docker ----------
Write-Host "[INFO] Checking Docker status..."
try {
    docker info | Out-Null
} catch {
    Write-Warning "Docker does not appear to be running."
    $dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerPath) {
        Write-Host "[INFO] Starting Docker Desktop..."
        Start-Process -FilePath $dockerPath -WindowStyle Normal
    } else {
        Write-Error "Docker Desktop executable not found at $dockerPath."
        exit 1
    }

    Write-Host "[INFO] Waiting for Docker to become ready..."
    while ($true) {
        Start-Sleep -Seconds 5
        try {
            docker info | Out-Null
            break
        } catch {
            Write-Host "[INFO] Still waiting for Docker..."
        }
    }
}
Write-Host "[INFO] Docker is running."

# ---------- Start containers ----------
Write-Host "[INFO] Starting required Docker containers (docker‑compose)..."
docker compose up -d --remove-orphans
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to start Docker containers."
    exit 1
}

# ---------- Launch daemon ----------
Write-Host "[INFO] Launching swarm daemon (smart_executor)..."
$daemon = Start-Process -FilePath "python" -ArgumentList "-m", "smart_executor" -NoNewWindow -PassThru
if (-not $daemon) {
    Write-Error "Failed to start the daemon process."
    exit 1
}

# ---------- Wait for port 8080 ----------
Write-Host "[INFO] Waiting for daemon to listen on port 8080..."
while (-not (Test-NetConnection -ComputerName localhost -Port 8080 -InformationLevel Quiet)) {
    Write-Host "[INFO] Port 8080 not yet open – retrying in 2 seconds..."
    Start-Sleep -Seconds 2
}
Write-Host "[INFO] Daemon is ready."

# ---------- Open dashboard ----------
Write-Host "[INFO] Opening dashboard in default browser..."
Start-Process "http://localhost:8080"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Swarm environment started successfully!" -ForegroundColor Green
Write-Host "   Keep this PowerShell window open for live status." -ForegroundColor Green
Write-Host "   Close it when you no longer need the console." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan

# Prevent script from exiting immediately so the user can see status
Read-Host "Press ENTER to close this window"