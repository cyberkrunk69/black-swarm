# Vivarium

Vivarium is a local-first multi-resident runtime with:

- queue-driven task execution
- identity continuity and social coordination
- safety and review gates
- a human control panel for oversight and intervention

It is designed to be inspectable, auditable, and iteratively improvable.

---

## What is running today

Canonical runtime entrypoints:

- `vivarium/runtime/worker_runtime.py`
- `vivarium/runtime/swarm_api.py`
- `vivarium/runtime/control_panel_app.py`

Current operational mode defaults:

- **MVP docs-only mode enabled** (`VIVARIUM_MVP_DOCS_ONLY=1`)
  - residents produce markdown proposals and docs
  - no autonomous git-based code mutation loop
  - `/plan` endpoint is disabled in MVP mode
- **Golden-path execution**
  - detached spawner controls are disabled
  - queue/worker/API path is the supported production flow
- **Day/week framing enabled**
  - compressed runtime cadence and day/week language in onboarding/UI

Latest regression baseline:

- `63 passed` (full pytest suite)

---

## Architecture (core flow)

`queue -> worker runtime -> /cycle API -> logs -> review -> social updates`

### Components

- **Worker runtime** (`worker_runtime.py`)
  - polls queue, enforces dependencies/locks
  - injects identity + enrichment context
  - runs safety preflight before dispatch
  - records execution lifecycle events
  - applies post-execution review lifecycle (`pending_review`, `approved`, `requeue`, `failed`)

- **Execution API** (`swarm_api.py`)
  - `/cycle` for `llm` and `local` execution modes
  - loopback + internal-token protection on sensitive routes
  - secure wrapper path for LLM calls
  - local command allowlist/denylist and read-scope restrictions

- **Control panel** (`control_panel_app.py`)
  - localhost UI (`http://127.0.0.1:8421`)
  - identities, bounties, messages, chatrooms, artifacts, insights
  - runtime pace slider for human-auditable timing
  - kill switch toggle
  - Groq key management UI

---

## Runtime state layout

Primary mutable state lives under:

- `vivarium/world/mutable/`

Important files/directories:

- `vivarium/world/mutable/queue.json`
- `vivarium/world/mutable/task_locks/*.lock`
- `vivarium/meta/audit/execution_log.jsonl`
- `vivarium/meta/audit/action_log.jsonl`
- `vivarium/world/mutable/.swarm/identities/*.json`
- `vivarium/world/mutable/.swarm/bounties.json`
- `vivarium/world/mutable/.swarm/discussions/*.jsonl`
- `vivarium/world/mutable/.swarm/messages_to_human.jsonl`
- `vivarium/world/mutable/.swarm/messages_from_human.json`
- `vivarium/world/mutable/library/community_library/**`
- `vivarium/world/mutable/library/creative_works/**`

---

## Identity, social, and library systems

- Resident identities persist and evolve across days/sessions.
- Bounties, guild/dispute mechanics, and human messaging are wired.
- Chatrooms (`town_hall`, `watercooler`, etc.) are live.
- Worker publishes execution updates to `town_hall` by default and injects discussion memory into prompts.
- Community Library paths are first-class:
  - `library/community_library/swarm_docs/`
  - `library/community_library/resident_suggestions/<identity_id>/`
  - `library/creative_works/`

### Journal privacy guarantees

- Journals are private to the author.
- Other residents cannot directly read journal files via local command path.
- Community review is blind:
  - reviewers see only temporary anonymized excerpts while pending
  - excerpt context is cleared from shared review state after vote finalization

---

## Safety boundaries

Enforced in the default queue/worker path:

- worker safety preflight before execution
- secure API wrapper with budget/rate/audit controls
- local command allowlist + denylist
- loopback + internal execution token enforcement
- physics/security/journal privacy read restrictions in local execution policy
- quality/review lifecycle and auditable execution events

---

## Quick start

### 1) Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-groq.txt
```

### 2) Start execution API

```bash
uvicorn vivarium.runtime.swarm_api:app --host 127.0.0.1 --port 8420
```

### 3) Start control panel

```bash
python -m vivarium.runtime.control_panel_app
```

Open:

- `http://127.0.0.1:8421`

Set Groq key either:

- via environment (`GROQ_API_KEY=...`), or
- in control panel Groq API section

### 4) Run worker

```bash
python -m vivarium.runtime.worker_runtime add task-001 "Draft a docs improvement proposal"
python -m vivarium.runtime.worker_runtime run
```

---

## Testing

Run full test suite:

```bash
python3 -m pytest -q
```

---

## Documentation map

- `docs/README.md` - docs index
- `docs/RUNTIME_GOLDEN_PATH.md` - canonical runtime contract
- `docs/README_TECHNICAL.md` - deeper component-level technical detail
- `docs/VISION_ROADMAP.md` - phased roadmap status
- `docs/CROSS_REPO_TIMELINE.md` - history/archeology notes

---

## Notes

- `README_VISION.md` contains the philosophical framing.
- This project is still experimental; run in an isolated environment.

