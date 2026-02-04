#!/usr/bin/env bash
# -------------------------------------------------
# ONE-CLICK STARTUP SCRIPT – Unix (Linux/macOS/WSL)
# -------------------------------------------------
# Steps:
#   1. Load GROQ_API_KEY & INFERENCE_ENGINE from .env
#   2. Ensure Docker daemon is running
#   3. Wait for Docker to be ready
#   4. Start required docker‑compose services
#   5. Launch the swarm daemon (smart_executor)
#   6. Wait for port 8080 to be listening
#   7. Open the dashboard in the default browser
#   8. Show live status & handle errors
# -------------------------------------------------

set -euo pipefail

# Helper for coloured output
info()   { echo -e "\e[34m[INFO]  $*\e[0m"; }
warn()   { echo -e "\e[33m[WARN]  $*\e[0m"; }
error()  { echo -e "\e[31m[ERROR] $*\e[0m" >&2; }

info "Starting Swarm Environment …"

# ---------- Load .env ----------
ENV_FILE="$(dirname "$0")/.env"
if [[ -f "$ENV_FILE" ]]; then
    while IFS='=' read -r key value; do
        # ignore comments and empty lines
        [[ -z "$key" ]] && continue
        [[ "$key" =~ ^# ]] && continue
        case "$key" in
            GROQ_API_KEY) export GROQ_API_KEY="$value" ;;
            INFERENCE_ENGINE) export INFERENCE_ENGINE="$value" ;;
        esac
    done < "$ENV_FILE"
else
    error ".env file not found at $ENV_FILE. Please create one with GROQ_API_KEY."
    exit 1
fi

: "${INFERENCE_ENGINE:=auto}"

# ---------- Check Docker ----------
info "Checking Docker daemon..."
if ! docker info >/dev/null 2>&1; then
    warn "Docker does not appear to be running."
    # Try to start Docker (Linux: systemctl, macOS: open -a Docker)
    if command -v systemctl >/dev/null; then
        info "Attempting to start Docker via systemctl..."
        sudo systemctl start docker
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        info "Attempting to start Docker Desktop on macOS..."
        open -a Docker
    else
        error "Unable to automatically start Docker on this platform."
        exit 1
    fi

    info "Waiting for Docker to become ready..."
    until docker info >/dev/null 2>&1; do
        sleep 5
        info "Still waiting for Docker..."
    done
fi
info "Docker is running."

# ---------- Start containers ----------
info "Starting required Docker containers (docker‑compose)..."
docker compose up -d --remove-orphans
if [[ $? -ne 0 ]]; then
    error "Failed to start Docker containers."
    exit 1
fi

# ---------- Launch daemon ----------
info "Launching swarm daemon (smart_executor)..."
# Run daemon in background; redirect output to a log file for live status
LOG_FILE="$(dirname "$0")/daemon.log"
nohup python -m smart_executor >>"$LOG_FILE" 2>&1 &
DAEMON_PID=$!
info "Daemon PID: $DAEMON_PID (log: $LOG_FILE)"

# ---------- Wait for port 8080 ----------
info "Waiting for daemon to listen on port 8080..."
while ! ss -ltn | awk '{print $4}' | grep -q ':8080'; do
    sleep 2
    info "Port 8080 not yet open – retrying..."
done
info "Daemon is ready."

# ---------- Open dashboard ----------
if command -v xdg-open >/dev/null; then
    info "Opening dashboard in default browser..."
    xdg-open http://localhost:8080
elif command -v open >/dev/null; then
    open http://localhost:8080
else
    warn "Could not detect a command to open a browser automatically."
fi

info "Swarm environment started successfully!"
info "Live daemon output follows (press Ctrl+C to stop monitoring):"
tail -f "$LOG_FILE"