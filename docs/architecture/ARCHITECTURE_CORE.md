# Black Swarm Core Architecture (Antidote)

This document describes the current, supported runtime. Anything not
listed here is considered legacy or experimental and lives under
`docs/ideas/` or `docs/legacy/`.

## Components

- **orchestrator.py**: Spawns workers, validates config, and manages the queue.
- **worker.py**: Claims tasks using file locks, calls `/grind`, and appends status
  events to JSONL.
- **swarm.py**: FastAPI server exposing `POST /grind` and calling Groq's
  OpenAI-compatible API.

## Core Files and Directories

- **queue.json**: Source-of-truth task queue (write by orchestrator or manual edits).
- **execution_log.jsonl**: Append-only execution events.
- **task_locks/**: Atomic lock files for task claiming.

## High-Level Flow

1. Add tasks to `queue.json` (e.g., `python orchestrator.py add ...`).
2. Start the Swarm API (`uvicorn swarm:app --host 127.0.0.1 --port 8420`).
3. Start the orchestrator (`python orchestrator.py start 4`).
4. Each worker:
   - Reads `queue.json`
   - Checks dependencies and completion status
   - Acquires a lock using `O_CREAT | O_EXCL`
   - Calls `/grind` with `prompt` and optional `model`
   - Appends an event to `execution_log.jsonl`
   - Releases the lock

## Locking (Race Condition Prevention)

Lock files live in `task_locks/` and contain a small JSON blob:

```json
{
  "task_id": "task_001",
  "worker_id": "worker_ab12cd34",
  "started_at": "2026-02-08T12:00:00+00:00"
}
```

Workers use atomic file creation (`os.O_CREAT | os.O_EXCL`) so only one
worker can claim a task at a time. Stale locks are removed after
`LOCK_TIMEOUT_SECONDS`.

## Data Formats

### queue.json

```json
{
  "version": "1.0",
  "api_endpoint": "http://127.0.0.1:8420",
  "tasks": [
    {
      "id": "task_001",
      "type": "grind",
      "prompt": "Summarize the repository changes",
      "min_budget": 0.05,
      "max_budget": 0.10,
      "intensity": "medium",
      "status": "pending",
      "depends_on": [],
      "parallel_safe": true,
      "model": "llama-3.1-8b-instant"
    }
  ]
}
```

### execution_log.jsonl

Each line is a standalone JSON object:

```json
{"task_id":"task_001","worker_id":"worker_ab12cd34","status":"in_progress","timestamp":"2026-02-08T12:00:00+00:00"}
{"task_id":"task_001","worker_id":"worker_ab12cd34","status":"completed","timestamp":"2026-02-08T12:00:10+00:00","result_summary":"...","errors":null,"model":"llama-3.1-8b-instant"}
```

## Constraints (Current State)

- Workers never modify `queue.json` (read-only).
- Logging is append-only JSONL (no shared JSON object writes).
- **Groq-only** inference with strict model whitelist.
- No `/plan` endpoint or shell execution of tasks.

## Failure Behavior

- Worker exceptions are loud and terminate the worker.
- Orchestrator reports timeouts and errors explicitly.
- No silent error swallowing (`except: pass`) in the core runtime.
