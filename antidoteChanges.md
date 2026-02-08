# Antidote Changes

This file explains what was changed to reach a clean, working baseline and
why the previous state hindered progress.

## Summary

The repo was overloaded with conflicting experiments, duplicate systems,
and unsafe execution paths. The antidote pass removes non-core code,
hardens the runtime, and isolates speculative ideas into a dedicated
docs structure.

## Key Changes (and Why)

### 1) Core Runtime Only
**Change:** Kept only the orchestrator/worker loop and Groq-only API server.  
**Why it mattered:** The previous repo contained dozens of overlapping
executors, schedulers, and spawners. That made it impossible to reason
about which code actually ran, and introduced competing defaults.

### 2) Groq-Only Inference Path
**Change:** Enforced a hard model whitelist and removed other providers
and CLI paths.  
**Why it mattered:** Multiple model backends created silent fallbacks and
policy drift. A strict whitelist guarantees deterministic behavior.

### 3) Safe Task Execution
**Change:** Removed shell execution of user input and replaced with
direct Groq API calls.  
**Why it mattered:** The old server executed tasks via `subprocess` with
`shell=True`, which is unsafe and non-deterministic.

### 4) Loud Failures and JSONL Logging
**Change:** Switched execution logging to append-only JSONL and removed
silent exception swallowing.  
**Why it mattered:** Single JSON logs were vulnerable to corruption under
concurrency. JSONL allows atomic appends and keeps a reliable audit trail.

### 5) Lock Safety
**Change:** Ensured locks always release in `finally` and added worker
timeouts.  
**Why it mattered:** A leaked lock could deadlock the entire run and stall
progress indefinitely.

### 6) Documentation Rebuild
**Change:** Moved speculative plans and legacy docs into:
`docs/ideas/` and `docs/legacy/`. Added a clean, current README.  
**Why it mattered:** The old docs described features that did not exist,
creating constant false leads and wasted effort.

### 7) Garbage and Noise Removal
**Change:** Removed hundreds of unused scripts, logs, extracted code,
and experimental artifacts.  
**Why it mattered:** These files obscured the real execution path and
slowed down audits and refactors.

## Current State

- **Core runtime**: `orchestrator.py`, `worker.py`, `swarm.py`
- **Groq-only**: strict model whitelist in `config.py`
- **Logs**: `execution_log.jsonl` (append-only)
- **Docs**: current design in `docs/architecture/ARCHITECTURE_CORE.md`
- **Ideas**: centralized in `docs/ideas/index.md`
