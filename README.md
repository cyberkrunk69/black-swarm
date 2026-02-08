# Black Swarm (Antidote)

Minimal, hardened swarm runtime with a strict Groq-only inference path.
This repo contains the **core** orchestrator/worker loop and a safe API
server. Everything else is separated into `docs/ideas/` and `docs/legacy/`.

## Current Core

- `orchestrator.py`: Spawns workers and manages the queue
- `worker.py`: Claims tasks via file locks and calls the API
- `swarm.py`: FastAPI server exposing `POST /grind`

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.template .env
# Edit .env and set GROQ_API_KEY

uvicorn swarm:app --host 127.0.0.1 --port 8420
```

Add a task and run workers:

```bash
python orchestrator.py add task_001 grind --prompt "Summarize this repo"
python orchestrator.py start 4
python orchestrator.py status
```

## Core Data Files

- `queue.json` - task queue
- `execution_log.jsonl` - append-only execution log
- `task_locks/` - atomic lock files created by workers

## Model Policy (Groq Only)

Allowed models (hard whitelist in `config.py`):

- `llama-3.1-8b-instant`
- `llama-3.3-70b-versatile`
- `openai/gpt-oss-120b`
- `openai/gpt-oss-20b`

## Documentation

- `docs/architecture/ARCHITECTURE_CORE.md` - current, supported design
- `docs/ideas/index.md` - future-facing ideas and plans
- `docs/legacy/` - historical reports and notes (not current)

## Non-Goals

- No `/plan` endpoint
- No shell execution of tasks
- No non-Groq model providers
