FROM python:3.11-slim-bookworm

WORKDIR /app

# =============================================================================
# BLACK SWARM - Safe-by-default container runtime
#
# Security notes:
# - Avoids `curl | bash` installers.
# - Does NOT auto-install external CLIs (e.g. Claude Code) during image build.
# =============================================================================

# Minimal system dependencies (keep this list tight)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (API server + optional dashboard dependencies)
COPY requirements.txt requirements-groq.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-groq.txt

# Copy application code
COPY . .

# Fix line endings and make entrypoint executable
RUN sed -i 's/\r$//' docker-entrypoint.sh && chmod +x docker-entrypoint.sh

# Create directories
RUN mkdir -p /app/grind_logs /app/knowledge /app/experiments /app/data

# Create non-root user for security (UID 1000 matches most host users)
RUN useradd -m -u 1000 swarm && \
    chown -R swarm:swarm /app/grind_logs /app/experiments /app/data && \
    chmod +x docker-entrypoint.sh

# Environment
ENV PYTHONUNBUFFERED=1
ENV WORKSPACE=/app
# Default to auto engine selection
ENV INFERENCE_ENGINE=auto

# Switch to non-root user (critical security hardening)
USER swarm

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python", "-m", "uvicorn", "swarm:app", "--host", "0.0.0.0", "--port", "8420"]
