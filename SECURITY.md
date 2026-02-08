# Security Notes (Safe-by-default)

This repository contains code that can start local servers and run automation.
To keep **local runs safe**, the defaults are intentionally conservative.

## What was hardened

- **Docker build**: the `Dockerfile` no longer uses `curl | bash` installers and no longer auto-installs external CLIs (e.g. `@anthropic-ai/claude-code`) during image build.
- **Local servers**: the control panel now **binds to `127.0.0.1` by default**, not `0.0.0.0`.
- **Remote execution**: legacy `remote_execution*.py` relay/client modules were removed from the repo root.
- **Docker compose**: ports are mapped to **`127.0.0.1` only** so services aren’t exposed to your LAN unless you explicitly change the mappings.

## Running safely

- **Recommended**: run services bound to localhost and only expose ports you intend to use.
- **Docker**: `docker compose up` maps:
  - API: `127.0.0.1:8420`
  - Control panel: `127.0.0.1:8421`

## Explicitly enabling non-local binding (opt-in)

Some services support LAN binding for controlled environments. This should be opt-in.

- **Control panel**:
  - Set `SWARM_CONTROL_PANEL_HOST=0.0.0.0` to listen on all interfaces.
  - Prefer keeping Docker port mappings on `127.0.0.1` unless you really intend LAN access.

- **LAN server**:
  - Default binds to `127.0.0.1`.
  - To allow LAN clients, set:
    - `LAN_BIND_HOST=0.0.0.0`
    - `LAN_WHITELIST_CIDRS="192.168.1.0/24"` (or a tighter allowlist), **or**
    - `LAN_ALLOW_PRIVATE_RANGES=1` (broad; not recommended)

## Guardrails

`tools/security_scan.py` performs a lightweight scan for high-risk patterns (e.g. `curl | bash`, NodeSource installers, auto-installing `@anthropic-ai/claude-code`).

