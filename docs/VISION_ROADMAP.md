# Vivarium Vision Roadmap

Last updated: 2026-02-10

This roadmap now reflects the **current real runtime state** (what is actually wired and tested), not only the intended architecture.

Cross-repo archaeology and anomaly evidence are tracked in `./CROSS_REPO_TIMELINE.md`.

---

## North-star outcomes

1. **Reliable execution core**  
   Deterministic, auditable task execution with clear runtime contracts.

2. **Aligned autonomy**  
   Residents can act creatively, but inside explicit human-defined safety boundaries.

3. **Compounding capability**  
   Repeated work should become reusable capability over time.

4. **Civic social layer**  
   Identity, journals, bounties, guilds, discussions, and dispute systems improve coordination quality.

5. **Transparent governance**  
   Safety checks, review states, and social/economic actions are inspectable from logs/state.

---

## Runtime snapshot (verified)

- Canonical runtime path is established and active:
  - `vivarium/runtime/worker_runtime.py`
  - `vivarium/runtime/swarm_api.py`
  - `vivarium/runtime/control_panel_app.py`
- Golden-path enforcement is active (detached spawner controls are disabled in UI/API).
- Day/week framing is active (compressed day cadence).
- MVP docs-only mode is active by default:
  - no autonomous git mutations
  - planning endpoint (`/plan`) disabled in MVP mode
  - residents write markdown proposals/journals (Community Library paths below)
- Community Library texture is live:
  - `library/community_library/swarm_docs/`
  - `library/community_library/resident_suggestions/<identity_id>/`
  - `library/creative_works/` (creative archive)
- Social/chat systems are wired:
  - chatrooms API reads `.swarm/discussions/*.jsonl`
  - worker injects shared discussion context into prompts
  - worker auto-posts task updates to `town_hall` by default
- Control panel includes:
  - kill switch, insights strip, artifacts, chatrooms, bounties, messages
  - runtime pace slider (human auditability)
  - Groq key UI flow (set/clear/status)
  - identity forge UI (resident-authored identities)
- Current regression baseline: `62 passed` (full pytest suite).

---

## Phase status matrix (real state)

| Phase | Status | Real state today | Remaining gap |
| --- | --- | --- | --- |
| Phase 0 - Canonical runtime | Implemented | Golden path is clear and documented; canonical runtime entrypoints are active. | Keep deprecated runners isolated; continue smoke checks. |
| Phase 1 - Hard safety wiring | Implemented (MVP) | Worker preflight + API safety + SecureAPIWrapper + local command policies are wired. | Continue tightening policy coverage and threat-model tests. |
| Phase 2 - Quality/critic lifecycle | Implemented (initial) | `pending_review -> approved/requeue/failed` lifecycle and quality gate integration are active in worker flow. | Broaden verifier heuristics and integration/e2e gate depth. |
| Phase 3 - Tool-first compounding | Partially implemented | Tool router + skill registry path works and is tested. | Default MVP mode disables tool routing; promotion-to-skill loops remain limited. |
| Phase 4 - Intent/decomposition | Implemented (initial) | Intent extraction/injection + deterministic decomposition + dependency-aware subtasks are wired. | Expand planning quality and long-horizon decomposition robustness. |
| Phase 5 - Social/economic systems | Implemented (initial) | Bounties, identity/profile loops, human messaging, discussions, phase5 reward hooks, and chat memory are live. | Continue invariants/audit hardening and governance UX clarity. |
| Phase 6 - Multi-user/LAN + vision dashboard | Not started | No production multi-user/LAN mode or dedicated vision dashboard route. | Reintroduce behind strict feature flags + threat model. |
| Phase 7 - Autonomous improvement loops | Intentionally gated (MVP) | Self-directed code-change autonomy is intentionally disabled in MVP docs-only mode. | Add explicit human checkpoints and rollback workflow before enabling. |

---

## Per-phase detail (current)

### Phase 0 - Stabilize one truth

**Shipped**
- Canonical runtime path enforced.
- Golden-path-only control posture in control panel APIs.
- Queue/execution contract centered in `runtime_contract.py`.

**Open**
- Continue explicit deprecation/isolation of alternate orchestration code.

---

### Phase 1 - Hard safety in execution

**Shipped**
- Worker dispatch performs safety preflight.
- `/cycle` enforces loopback + internal token checks.
- SecureAPIWrapper mediates LLM calls.
- Local command allowlist/denylist with MVP read-scope restrictions is active.

**Open**
- Expand adversarial policy tests and document edge-case behavior.

---

### Phase 2 - Quality gates + critic lifecycle

**Shipped**
- Post-execution review emits `pending_review` events.
- Review can `approved`, `requeue`, or `failed` after retry limit.
- Quality gate state updates recorded.

**Open**
- Improve reviewer depth and richer quality gate progression beyond initial lifecycle.

---

### Phase 3 - Tool-first compounding

**Shipped**
- `tool_router` and skill registry contract import/route successfully.
- Tool context can be injected into prompt path.

**Open**
- In default MVP docs-only mode, tool routing is disabled by policy.
- Capability promotion/compounding metrics need deeper production tracking.

---

### Phase 4 - Intent to decomposition

**Shipped**
- Intent extraction/injection is wired.
- Deterministic phase-4 gut checks and feature breakdown are implemented.
- Dependency-aware subtask compilation is active.

**Open**
- Improve decomposition quality for very large cross-cutting requests.

---

### Phase 5 - Social/economic systems

**Shipped**
- Identity profiles, journals, bounties, guild/dispute flows, and human messaging are wired.
- Chatrooms (`town_hall`, `watercooler`, etc.) are active in control panel.
- Discussion memory is injected into resident prompts; residents can respond to each other via shared context.
- Worker can auto-publish execution updates into `town_hall`.
- Community Library pathing is in prompt context and artifact flows.

**Open**
- Continue tightening social invariants and moderation/governance UX.

---

### Phase 6 - Multi-user/LAN + vision dashboard

**Current**
- Not enabled in production path.

**Next**
- Recover historical design intent behind feature flags and modern threat model.

---

### Phase 7 - Autonomous improvement with human checkpoints

**Current**
- Intentionally restricted in MVP docs-only mode (proposal-first, no autonomous code mutation loop).

**Next**
- Introduce explicit propose -> review -> approve/apply pipeline with rollback plans for high-risk surfaces.

---

## Near-term execution order (updated)

1. Keep Phase 0-5 reliability hard (regressions, policy tests, observability).
2. Improve Phase 5 governance ergonomics (discussion quality, moderation, audit replay).
3. Build feature-flagged Phase 6 experiments (LAN/vision) without weakening current safety model.
4. Only then evaluate scoped Phase 7 rollout with mandatory human checkpoints.

---

## Non-goals (still enforced)

- No big-bang rewrite.
- No blind restore of backup-era artifacts.
- No autonomy expansion ahead of safety/quality/governance checkpoints.

