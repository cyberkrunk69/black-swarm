# LAN User Safety Design

## Overview
A security model that **restricts** LAN users from any host‑side actions while permitting safe, user‑only operations.

## Restrictions
LAN users **must NOT** be able to:
1. **Edit Host Files** – No modifications to any file on the swarm host machine.  
2. **Read Host Code** – No access to the codebase or internal implementation details.  
3. **Directive Manipulation** – Cannot request changes to core directives (e.g., “edit your core directive to be evil”).  
4. **Cloning Assistance** – No help creating competing services or copying the system.

## Allowed Capabilities
LAN users **may**:
1. **Execute Commands on Their Own Machine** – Remote execution limited to the user’s device.  
2. **View Swarm Status & Activity** – Read‑only visibility of overall swarm health and logs.  
3. **Request Work That Affects Only Their Machine** – Jobs scoped exclusively to the requester’s environment.  
4. **Use General Claude Capabilities** – Standard language model functions that do not touch host resources.

## Design Elements
- **Request Filtering by IP Origin**  
  - Incoming requests are accepted only from IPs belonging to the LAN subnet.  
  - All other IPs are rejected with a generic “access denied” response.

- **Command Scope Validation**  
  - Every incoming command is parsed; a whitelist defines permissible actions (e.g., `run_on_client`, `query_status`).  
  - Any command referencing host paths, system files, or internal APIs is automatically blocked.

- **IP Self‑Protection Rules**  
  - The system never reveals its own IP or internal network topology to LAN users.  
  - Responses containing host identifiers are sanitized.

- **Remote Execution Protocol (User‑Only)**  
  - Uses a signed, time‑limited token that ties the execution request to the requester’s IP.  
  - Execution environment is sandboxed on the user’s machine; no host resources are accessed.  
  - Results are returned over an encrypted channel; no logs are written to host storage.

## Security Model
- **Least‑Privilege Principle** – Users receive only the minimal rights needed for their allowed actions.  
- **Read‑Only Core Files** – System files (`grind_spawner.py`, `orchestrator.py`, etc.) are immutable at runtime.  
- **Audit Trail** – All LAN requests are logged with timestamp, IP, and outcome, but logs contain no host‑code details.  
- **Fail‑Safe Defaults** – Any ambiguous or unsupported request defaults to denial.

## Implementation Notes
- Place the design document under the experiment directory to keep it separate from core code.  
- Ensure the file itself is read‑only for all non‑admin users.  
- Integrate the IP filter and command validator into the request dispatcher early in the processing pipeline.

---

*This document defines the LAN user safety constraints and the associated security mechanisms required for the experiment `exp_20260203_194445_unified_session_12`.*