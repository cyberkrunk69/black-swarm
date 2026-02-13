# Devtools

Developer utilities for Vivarium. Each script produces a single `.md` artifact. Output directories are gitignored.

[![Draft System Tests](https://img.shields.io/badge/draft%20tests-21%20passed-brightgreen)](./#testing-the-draft-system)

## Directory Structure

```
devtools/
├── branch-status.sh            # User-facing launchers (top level)
├── ci-status.sh
├── commit-message-gen.sh
├── pr-message-gen.sh
├── repo-map.sh
├── scout-nav                   # Scout navigation CLI (find code in 2s)
├── scout-index                 # Local code search (ctags + SQLite, zero LLM)
├── scout-brief                 # Scout investigation plan CLI (briefing for expensive models)
├── scout-doc-sync              # Doc sync (generate .tldr.md / .deep.md via LLM)
├── scout-commit                # Scout commit CLI (assemble message from docs/drafts/*.commit.txt)
├── scout-pr                    # Scout PR CLI (assemble description from docs/drafts/*.pr.md)
├── scout-status                # Scout workflow dashboard (doc-sync, drafts, spend, hooks)
├── scout-ci-guard              # CI validation (.tldr coverage, confidence, spend)
├── scout-smoke-test.sh         # End-to-end smoke test for draft system (works offline)
├── scout-roast                 # Scout Roast CLI (efficiency reports + impact-aware critique)
├── ci-status.command           # One-click launcher (double-click in Finder)
├── ci-status-gui.app           # GUI launchers (one-click from Finder)
├── branch-status-gui.app
├── repo-map-gui.app
├── commit-message-gen-gui.app
├── pr-message-gen-gui.app
├── scripts/                    # CLI/script utilities (helpers, find_python, etc.)
├── hooks/                      # Git hooks (post-commit, prepare-commit-msg)
├── ci/                         # CI-specific runners (scout-ci-guard, run_tests, lint)
├── gui/                        # Optional: GUI asset bundlers
├── _internal/                  # Internal logic, shared libs, supporting files
│   ├── ci-status/              # Dry-run + execute split, ci-status-lib.py
│   ├── common/                 # utils.sh, api-confirm.sh
│   ├── commit-message-gen/     # commit-message-lib.py
│   └── pr-message-gen/         # pr-message-lib.py
└── README.md
```

## Usage

**One-click execution:** Double-click the `.app` files in Finder:

- `ci-status-gui.app` — CI/CD status (native dialog for cost confirmation)
- `branch-status-gui.app` — Branch status, PR info, diff-stat
- `repo-map-gui.app` — Structural inventory for Python/GitHub repos
- `commit-message-gen-gui.app` — Generate conventional commit message from staged changes
- `pr-message-gen-gui.app` — Generate PR description from branch, CI, and repo map

**Command line:** Run the scripts in `devtools/`:

- `./devtools/ci-status.sh` or `CI_STATUS_BRANCH=main ./devtools/ci-status.sh`
- `./devtools/branch-status.sh` or `BASE_BRANCH=main ./devtools/branch-status.sh`
- `./devtools/repo-map.sh`
- `./devtools/commit-message-gen.sh` — requires staged files (`git add` first)
- `./devtools/pr-message-gen.sh`
- `./devtools/scout-nav --task "fix auth timeout bug"` — Scout navigation (uses scout-index when possible, else GROQ_API_KEY)
- `./devtools/scout-index build` — Build local code index (ctags + SQLite)
- `./devtools/scout-index query "auth token"` — Search symbols (no API calls)
- `./devtools/scout-brief --task "fix race condition in token refresh"` — Investigation plan (requires GROQ_API_KEY)
- `./devtools/scout-doc-sync generate -t vivarium/scout/` — Generate docs (.tldr.md, .deep.md, module briefs)
- `./devtools/scout-commit` — Commit using assembled drafts from docs/drafts/*.commit.txt
- `./devtools/scout-commit --preview` — Preview assembled message (no commit)
- `./devtools/scout-pr` — PR description from docs/drafts/*.pr.md (stdout)
- `./devtools/scout-pr --preview` — Preview PR description (no browser)
- `./devtools/scout-status` — Workflow dashboard (doc-sync, drafts, spend, accuracy, hooks)
- `./devtools/scout-ci-guard` — CI validation (exits 0 if pass, 1 if fail)
- `./devtools/scout-roast --today` — Efficiency report (today/week/month, optional --compare)
- `./devtools/scout-roast -t vivarium/scout/router.py` — Impact-aware critique using living docs

## Testing the Draft System

Run the draft system test suite and smoke test:

```bash
pytest tests/scout/test_draft_*.py -v
./devtools/scout-smoke-test.sh
```

Smoke test works offline (no API key needed). When `GROQ_API_KEY` is set, it also exercises scout-doc-sync and prepare-commit-msg draft generation.

## Python Environment

Scout scripts (`scout-nav`, `scout-brief`, `scout-doc-sync`, `scout-commit`, `scout-pr`, `scout-status`, `scout-ci-guard`, `scout-index`, `scout-roast`) automatically use a project virtualenv when present:

- If `./venv/` or `./.venv/` exists in the repo root, the script uses that Python interpreter
- Otherwise, it falls back to `python3` from `PATH`

No manual activation needed. Create a venv and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # optional — scripts auto-detect venv
pip install -e . && pip install -r requirements-groq.txt
./devtools/scout-doc-sync generate -t vivarium/scout/
```

If you see `ModuleNotFoundError` or import errors, ensure the vivarium package and dependencies (e.g. `httpx`) are installed in the interpreter being used (venv or system).

## Unified API Confirmation

Scripts that may incur API costs (e.g., ci-status with Groq) use a consistent confirmation system:

- **Environment variable:** `VIVARIUM_CONFIRM_AI=1` — Skip interactive prompt, auto-confirm API calls.
- **Interactive:** When run from terminal, prompts for confirmation before making API calls.
- **Non-interactive:** When stdin is piped (e.g. `echo "n" | ci-status.sh`), defaults to no API calls and uses programmatic extraction only.
- **Cost estimation:** Every script that uses APIs estimates and displays costs before proceeding.

## branch-status

Branch status, unmerged commits, PR info, and diff-stat vs base (master). Lean output (~10KB).

**Output:** `devtools/branch-status/branch-status_YYYY-MM-DD_HH-MM-SS.md`

## commit-message-gen

Generate a draft conventional commit message from staged changes. Uses programmatic diff analysis (path + content keywords) — no LLM. Infers type (feat, fix, docs, style, refactor, test, chore), scope from file paths, and suggests `BREAKING CHANGE` when appropriate.

**Output:** stdout (and clipboard on macOS)

**Requirements:** Staged files (`git add` first). Exits with error if nothing is staged.

**Options:** `COPY_CLIPBOARD=0` to disable clipboard copy.

## pr-message-gen

Generate a draft PR description from branch commits, CI status, and repo map. Runs `branch-status.sh`, `ci-status.sh`, and `repo-map.sh` to gather data, then formats a Markdown template with Summary, Affected Areas, CI Status, Testing checklist, and Related Issues. Uses programmatic parsing only — no LLM.

**Output:** `devtools/pr-message-gen/PR_DESCRIPTION_YYYYMMDD_HHMMSS.md` (and clipboard on macOS)

**Requirements:** `gh` optionally for CI status and related issues. Repo map requires macOS.

**Options:** `COPY_CLIPBOARD=0` to disable clipboard copy.

## scout-index

Local code search — zero LLM calls. Uses ctags + ripgrep + SQLite FTS5 for instant lookups (<100ms).

**Usage:**
- `./devtools/scout-index build` — Build index from scratch
- `./devtools/scout-index update` — Incremental update (git diff)
- `./devtools/scout-index query "auth token"` — Search symbols and files
- `./devtools/scout-index watch` — Background daemon, auto-update
- `./devtools/scout-index stats` — Show coverage

**Requirements:** `ctags` (Universal Ctags recommended: `brew install universal-ctags`). Optional: `rg` (ripgrep) for content search.

**Output:** Index stored in `.scout/index.db`. scout-nav uses it when confidence ≥80% (free); otherwise falls back to LLM ($0.002).

## scout-nav

Scout navigation CLI — find code in 2 seconds. Tries scout-index first (free); uses Groq LLM when index uncertain.

**Usage:**
- `./devtools/scout-nav --task "fix auth timeout bug"`
- `./devtools/scout-nav --task "add OAuth provider" --entry vivarium/runtime/`
- `./devtools/scout-nav --file vivarium/runtime/auth.py --question "where is token refresh?"`
- `./devtools/scout-nav --task "fix race condition" --json`
- `./devtools/scout-nav --task "optimize query" --output briefing.md`

**Requirements:** `GROQ_API_KEY` (env or runtime config), `httpx`, `vivarium`

**Output:** Pretty-printed result (default), JSON (with `--json`), or markdown briefing (with `--output`)

## scout-brief

Scout investigation plan CLI — generates comprehensive briefings for expensive models with git context, dependencies, and "Recommended Deep Model Prompt" section. Uses Groq (Llama 8B/70B) only; vendor-agnostic for expensive models.

**Usage:**
- `./devtools/scout-brief --task "fix race condition in token refresh"`
- `./devtools/scout-brief --task "add OAuth provider" --entry vivarium/runtime/auth/`
- `./devtools/scout-brief --pr 42 --output pr-briefing.md`
- `./devtools/scout-brief --task "optimize query" --output brief.md`

**Requirements:** `GROQ_API_KEY` (env or runtime config), `httpx`, `vivarium`

**Output:** Markdown briefing (stdout or file via `--output`)

## scout-commit

Scout commit CLI — assembles commit message from existing `docs/drafts/*.commit.txt` for staged .py files. No LLM calls; reads pre-generated drafts only.

**Usage:**
- `./devtools/scout-commit` — Commit using assembled drafts (default: `--use-draft`)
- `./devtools/scout-commit --preview` — Print assembled message to stdout without committing
- `./devtools/scout-commit --no-use-draft` — Skip draft assembly, run `git commit` (opens editor)

**Requirements:** Staged .py files (`git add` first). Drafts at `docs/drafts/{stem}.commit.txt` (generated by on-commit hooks).

**Output:** Commit message (preview) or runs `git commit -F <temp>`

### Autonomous workflow (prepare-commit-msg hook)

Install the prepare-commit-msg hook to auto-populate commit messages from scout-generated drafts when you run `git commit` (without `-m`):

```bash
cp devtools/hooks/prepare-commit-msg .git/hooks/prepare-commit-msg && chmod +x .git/hooks/prepare-commit-msg
```

When you run `git commit`, the hook: gets staged .py files, runs `_process_file` (generates drafts if needed), assembles `assemble_commit_message`, and writes to `.git/COMMIT_EDITMSG`. Respects `enable_commit_drafts` and `enable_pr_snippets` in config. Does not block commit on failure.

## scout-pr

Scout PR CLI — assembles PR description from existing `docs/drafts/*.pr.md` (or `.pr.txt`) for staged .py files. No LLM calls; reads pre-generated drafts only.

**Usage:**
- `./devtools/scout-pr` — Print assembled PR description (default: `--use-draft`)
- `./devtools/scout-pr --preview` — Same (always prints to stdout; no browser)
- `./devtools/scout-pr --no-use-draft` — Skip draft assembly

**Requirements:** Staged .py files (`git add` first). Drafts at `docs/drafts/{stem}.pr.md` or `.pr.txt` (generated by on-commit hooks).

**Output:** Markdown PR description to stdout

## scout-status

Scout workflow dashboard — git status–style view of doc-sync, drafts, spend, accuracy, and hooks.

**Usage:**
- `./devtools/scout-status`

**Output:** Doc-sync status (last .tldr.md/.deep.md mtime per staged file), missing commit drafts, hourly LLM spend, accuracy (last 24h), git hook status (prepare-commit-msg, post-commit).

## scout-ci-guard

CI validation — checks docs coverage, draft confidence, and spend limits. No LLM calls.

**Usage:**
- `./devtools/scout-ci-guard` — Validate vs origin/main
- `./devtools/scout-ci-guard --base-branch origin/develop`
- `./devtools/scout-ci-guard --hourly-limit 10 --min-confidence 0.8`

**Checks:** All .py files in changed PR paths have .tldr.md (unless ignored); no audit event has confidence < 0.7; hourly spend < $5 (configurable). Exits 0 if all pass, 1 + error message if any fail.

## scout-doc-sync (module briefs)

When processing a directory recursively, scout-doc-sync auto-generates module briefs (`__init__.py.module.md`) for each package directory after processing its files. Each brief summarizes: purpose, key components, and interaction flow. Written to `docs/livingDoc/<path>/__init__.py.module.md` and mirrored to `<package>/.docs/`. Controlled by `drafts.enable_module_briefs` in config.

## scout-roast

Scout Roast CLI — efficiency reports and impact-aware code critique. "Big AI hates this one simple trick."

**Usage:**
- `./devtools/scout-roast --today` — Today's savings report
- `./devtools/scout-roast --week` — This week
- `./devtools/scout-roast --month` — This month
- `./devtools/scout-roast --today --compare gpt-4` — Compare vs specific model
- `./devtools/scout-roast -t vivarium/scout/router.py` — LLM critique using living docs
- `./devtools/scout-roast -t file1.py -t file2.py --no-use-docs` — Critique without docs

**Requirements:** Audit log at `~/.scout/audit.jsonl` (for reports). GROQ_API_KEY for `--target` critique. Respects `roast.enable_roast` config.

**Output:** ASCII box report (reports) or LLM critique (risk, anti-patterns, improvements) when `--target` is used.

## repo-map

Pure structural inventory for Python/GitHub repos. Uses programmatic discovery (find, grep, awk) — no LLM. Output includes file tree, dependencies, workflows, imports, tests, docs, git signals, and markers (TODO/FIXME).

**Output:** `devtools/repo-map/repo-map_YYYY-MM-DD_HH-MM-SS.md`

## ci-status

CI/CD status for current branch (workflows, jobs, runs). Compact summaries for passing jobs; full details (workflow, job, conclusion, timestamps, failure logs) for failed jobs.

**Output:** `devtools/ci-status/ci-status_YYYY-MM-DD_HH-MM-SS.md`

Requires `gh` CLI (authenticated). Uses `gh run list` and `gh run view`.

### Analysis approach

- **Programmatic first:** Logs are filtered (noise, ANSI escape codes, timestamps) and condensed to failure-relevant blocks.
- **AI summarization (optional):** When `GROQ_API_KEY` is set and there are failed jobs, Groq API can summarize logs. Always prompts for confirmation (or respects `VIVARIUM_CONFIRM_AI=1`).
- **Fallback:** Programmatic extraction (coverage, AssertionError, ImportError patterns) when AI is declined or not configured.

### GUI (one-click)

Double-click `ci-status-gui.app` in Finder for a native macOS permission gate:

1. Runs the dry-run script to estimate cost
2. Shows a dialog: *"Estimated Groq API cost: $X.XX for N job(s). Execute with this cost? [Yes/No]"*
3. If **Yes**: opens Terminal and runs the execute script (auto-confirms)
4. If **No**: quits without making API calls

### Two-step process (dry-run + execute)

When using AI summarization, the workflow is split into two scripts for reliable terminal prompting:

1. **Dry run** — `./devtools/_internal/ci-status/ci-status-dry-run.sh`
   - Fetches runs, identifies failed ones, preprocesses logs, estimates costs
   - Prints estimated cost to the terminal
   - Saves job data to `/tmp/ci_status_plan_YYYYMMDD_HHMMSS.json`
   - Does **not** make any Groq API calls

2. **Execute** — `./devtools/_internal/ci-status/ci-status-execute.sh`
   - Finds the latest plan file in `/tmp`
   - Prompts: `Execute with estimated cost: $X.XX for N job(s)? [y/n]`
   - If `y` or `yes`, or `VIVARIUM_CONFIRM_AI=1`: makes Groq API calls and generates the summary markdown
   - If `n` or non-interactive: exits without making API calls (or uses programmatic extraction when called via orchestrated flow)

### AI summarization and costs

When `GROQ_API_KEY` is set, the execute script uses Groq's API (llama3-8b-8192) to summarize failed-job logs. **This incurs API costs.**

- **Pre-run confirmation:** The execute script (or `ci-status.sh` orchestrator) prompts before any Groq calls.
- **Token-efficient pre-processing:** Logs are filtered and condensed before calling the API.
- **Cost breakdown:** See the processing log (`.log` file) for per-request cost and token counts. The summary markdown ends with **Total API Cost Incurred: $X.XX** when costs were incurred.
