# Tiered File Permission System

## Overview
A lightweight, self‑contained permission framework that enables the system to modify its own code safely while preserving core safety guarantees.

## Tiers

### 1. **NEVER TOUCH**
*Absolute protection – any edit attempt is blocked and logged.*  
Typical files: `safety_gateway.py`, `safety_constitutional.py`, plus any other core‑safety modules.

### 2. **ASK PERMISSION**
*Editable only after an explicit, justified request.*  
Typical files: `smart_executor.py`, `inference_engine.py`, etc.  
Process:
1. **Request** – the requesting worker supplies:
   * `file_path`
   * `reason` – a short description of *why* the edit is needed.
2. **Review** – an independent reviewer worker evaluates the request.
3. **Debate** – a brief back‑and‑forth (max 2 rounds) between requester and reviewer to clarify intent.
4. **Decision**
   * **Granted** – the edit proceeds.
   * **Denied** – the attempt is logged; the original file remains unchanged.

### 3. **OPEN**
*No restrictions.*  
All new experiment files, output data, and exploratory scripts belong here.

## Rules
1. Core system files (`grind_spawner.py`, `orchestrator.py`, …) are **READ‑ONLY** (treated as *NEVER TOUCH*).
2. New files are created under `experiments/exp_20260203_194248_unified_session_3/` by default.
3. All permission actions are recorded in `permission_audit.log` (timestamp, worker, file, tier, outcome, reason).

---