"""
Scout Brief CLI — Generate Investigation Plans for expensive models.

Creates comprehensive briefings with git context, dependencies, and
"Recommended Deep Model Prompt" section. Uses Groq (Llama) only.
Vendor-agnostic: prepares the briefing; user chooses who consumes it.

Usage:
    ./devtools/scout-brief --task "fix race condition in token refresh"
    ./devtools/scout-brief --task "add OAuth provider" --entry vivarium/runtime/auth/
    ./devtools/scout-brief --pr 42 --output pr-briefing.md
    ./devtools/scout-brief --task "optimize query" --output brief.md
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from vivarium.scout.audit import AuditLog
from vivarium.scout.config import ScoutConfig
from vivarium.scout.validator import Validator
from vivarium.utils.llm_cost import estimate_cost

# Naive estimate for "expensive model exploration" sans Scout (used in savings calc)
ESTIMATED_EXPENSIVE_MODEL_COST = 0.85
COMPLEXITY_THRESHOLD = 0.7


@dataclass
class NavResult:
    """Navigation result from scout-nav."""

    target_file: str
    target_function: str
    line_estimate: int
    signature: str
    cost: float
    session_id: str
    reasoning: str
    suggestion: str
    confidence: int


@dataclass
class GitContext:
    """Git context for target file."""

    last_modified: str
    last_author: str
    last_commit_hash: str
    last_commit_msg: str
    churn_score: int  # 0-10
    files_changed_together: List[str]


@dataclass
class DepGraph:
    """Dependency graph for target file."""

    direct: List[str]
    transitive: List[str]
    callers: List[str]


def _generate_session_id() -> str:
    return str(uuid.uuid4())[:8]


def _run_git(repo_root: Path, *args: str) -> Tuple[bool, str]:
    """Run git command. Returns (success, output)."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0, (result.stdout or "").strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, ""


def gather_git_context(repo_root: Path, target_file: str) -> GitContext:
    """Gather git context: last commit, author, churn, co-changed files."""
    fp = repo_root / target_file
    if not fp.exists():
        return GitContext(
            last_modified="unknown",
            last_author="unknown",
            last_commit_hash="",
            last_commit_msg="",
            churn_score=0,
            files_changed_together=[],
        )

    # Last commit for file
    ok, log = _run_git(
        repo_root,
        "log",
        "-1",
        "--format=%h|%an|%ai|%s",
        "--",
        target_file,
    )
    if ok and log:
        parts = log.split("|", 3)
        hash_ = parts[0] if len(parts) > 0 else ""
        author = parts[1] if len(parts) > 1 else "unknown"
        date_str = parts[2] if len(parts) > 2 else "unknown"
        msg = parts[3] if len(parts) > 3 else ""
        # Normalize date: "2026-02-10 14:30:00 -0600" -> "2 days ago" style
        last_modified = date_str.split()[0] if date_str else "unknown"
        try:
            dt = datetime.strptime(last_modified, "%Y-%m-%d")
            delta = datetime.now(timezone.utc).date() - dt.date()
            days = delta.days
            if days == 0:
                last_modified = "today"
            elif days == 1:
                last_modified = "1 day ago"
            elif days < 7:
                last_modified = f"{days} days ago"
            elif days < 30:
                last_modified = f"{days // 7} weeks ago"
            else:
                last_modified = f"{days} days ago"
        except (ValueError, TypeError):
            pass
    else:
        hash_, author, last_modified, msg = "", "unknown", "unknown", ""

    # Churn: commit count in last 90 days
    ok, churn_log = _run_git(
        repo_root,
        "log",
        "--since=90 days ago",
        "--oneline",
        "--",
        target_file,
    )
    churn_count = len(churn_log.splitlines()) if ok and churn_log else 0
    churn_score = min(10, churn_count // 2)  # 0-10 scale

    # Files changed together in last commit
    ok, diff_names = _run_git(
        repo_root,
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "-r",
        "HEAD" if hash_ else "HEAD~1",
        "--",
        target_file,
    )
    files_together: List[str] = []
    if hash_:
        ok2, names = _run_git(
            repo_root,
            "show",
            "--name-only",
            "--format=",
            hash_,
        )
        if ok2 and names:
            files_together = [
                n.strip()
                for n in names.splitlines()
                if n.strip() and n.strip() != target_file
            ][:5]

    return GitContext(
        last_modified=last_modified,
        last_author=author,
        last_commit_hash=hash_,
        last_commit_msg=msg,
        churn_score=churn_score,
        files_changed_together=files_together,
    )


def _module_to_path(repo_root: Path, mod: str) -> Optional[str]:
    """Resolve module name to repo-relative path if file exists."""
    if not mod or mod.startswith("."):
        return None
    path_str = mod.replace(".", "/")
    for candidate in [
        repo_root / f"{path_str}.py",
        repo_root / path_str / "__init__.py",
    ]:
        if candidate.exists():
            try:
                return str(candidate.relative_to(repo_root))
            except ValueError:
                pass
    return None


def _parse_imports(content: str, repo_root: Path, current_file: str) -> List[str]:
    """Extract import targets and resolve to repo paths where possible."""
    import_re = re.compile(
        r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))\s"
    )
    results: List[str] = []
    seen: set = set()
    for line in content.splitlines():
        m = import_re.match(line)
        if m:
            mod = (m.group(1) or m.group(2) or "").split()[0]
            if not mod or mod.startswith("."):
                continue
            path = _module_to_path(repo_root, mod)
            if path and path not in seen:
                seen.add(path)
                results.append(path)
    return results[:15]


def _find_callers(repo_root: Path, target_file: str, limit: int = 10) -> List[str]:
    """Find files that import the target module."""
    target_mod = target_file.replace("/", ".").replace(".py", "")
    if target_mod.endswith(".__init__"):
        target_mod = target_mod[:-9]
    # Simple grep for import of this module
    callers: List[str] = []
    for py in repo_root.rglob("*.py"):
        if "__pycache__" in str(py) or "test" in str(py).lower():
            continue
        try:
            content = py.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in content.splitlines():
            if "import" in line and (
                target_mod in line or target_file.replace(".py", "") in line
            ):
                try:
                    rel = str(py.relative_to(repo_root))
                    if rel != target_file and rel not in callers:
                        callers.append(rel)
                        if len(callers) >= limit:
                            return callers
                except ValueError:
                    pass
    return callers


def _resolve_target_to_file(repo_root: Path, target_file: str) -> Optional[str]:
    """
    Resolve target to a valid Python file path. Handles directories and non-file targets.
    Returns repo-relative path to a file, or None if no suitable file found.
    """
    if not target_file:
        return None
    fp = repo_root / target_file
    if not fp.exists():
        return None
    if fp.is_file() and fp.suffix == ".py":
        try:
            return str(fp.relative_to(repo_root))
        except ValueError:
            return target_file
    if fp.is_dir():
        init_py = fp / "__init__.py"
        if init_py.exists():
            try:
                return str(init_py.relative_to(repo_root))
            except ValueError:
                pass
        # No __init__.py — can't analyze directory as file
        return None
    return None


def build_dependencies(repo_root: Path, target_file: str) -> DepGraph:
    """Build dependency graph: direct, transitive, callers."""
    resolved = _resolve_target_to_file(repo_root, target_file)
    if resolved is None:
        return DepGraph(direct=[], transitive=[], callers=[])
    target_file = resolved
    fp = repo_root / target_file
    if not fp.exists() or not fp.is_file():
        return DepGraph(direct=[], transitive=[], callers=[])

    content = fp.read_text(encoding="utf-8", errors="replace")
    direct = _parse_imports(content, repo_root, target_file)

    # Transitive: deps of direct (one level)
    transitive_set: set = set()
    for d in direct:
        dp = repo_root / d
        if dp.exists():
            try:
                c = dp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for imp in _parse_imports(c, repo_root, d):
                if imp not in direct and imp != target_file:
                    transitive_set.add(imp)
    transitive = list(transitive_set)[:10]

    callers = _find_callers(repo_root, target_file)

    return DepGraph(direct=direct, transitive=transitive, callers=callers)


def calculate_complexity(deps: DepGraph, git_ctx: GitContext) -> float:
    """Compute complexity score 0-1. >0.7 triggers 70B enhancement."""
    score = 0.0
    # Many dependencies
    score += min(0.3, (len(deps.direct) + len(deps.transitive)) * 0.03)
    # High churn
    score += git_ctx.churn_score / 30.0  # up to ~0.33
    # Many files changed together
    score += min(0.2, len(git_ctx.files_changed_together) * 0.05)
    # Many callers
    score += min(0.2, len(deps.callers) * 0.02)
    return min(1.0, score)


def _get_groq_api_key() -> Optional[str]:
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key
    try:
        from vivarium.runtime import config as runtime_config

        return runtime_config.get_groq_api_key()
    except ImportError:
        return None


async def _call_groq(
    prompt: str,
    model: str = "llama-3.1-8b-instant",
    system: Optional[str] = None,
) -> Tuple[str, float]:
    """Call Groq API. Returns (content, cost_usd)."""
    api_key = _get_groq_api_key()
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY not set. Set it in environment or configure via runtime."
        )
    try:
        import httpx
    except ImportError:
        raise RuntimeError("httpx required for scout-brief. Install with: pip install httpx")

    url = os.environ.get("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 800,
    }

    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
    resp.raise_for_status()
    data = resp.json()

    choice = data.get("choices", [{}])[0]
    msg = choice.get("message", {})
    content = msg.get("content", "").strip()

    usage = data.get("usage", {})
    # Groq Chat Completions uses prompt_tokens/completion_tokens (OpenAI format).
    # Responses API uses input_tokens/output_tokens. Support both.
    input_t = int(
        usage.get("prompt_tokens")
        or usage.get("input_tokens")
        or 0
    )
    output_t = int(
        usage.get("completion_tokens")
        or usage.get("output_tokens")
        or 0
    )

    cost = estimate_cost(model, input_t, output_t)
    if cost == 0.0 and content:
        cost = 1e-7  # Call was made, cost below precision or not reported

    return content, cost


def _format_structure_prompt(
    task: str,
    nav_result: NavResult,
    git_ctx: GitContext,
    deps: DepGraph,
) -> str:
    """Build prompt for 8B structure generation."""
    return f"""Task: {task}

Target file: {nav_result.target_file}
Function: {nav_result.target_function}
Lines: {nav_result.line_estimate}
Signature: {nav_result.signature}

Git context:
- Last modified: {git_ctx.last_modified} by @{git_ctx.last_author}
- Last commit: {git_ctx.last_commit_hash} — "{git_ctx.last_commit_msg}"
- Churn score: {git_ctx.churn_score}/10
- Files changed together: {', '.join(git_ctx.files_changed_together) or 'none'}

Dependencies:
- Direct: {', '.join(deps.direct) or 'none'}
- Transitive: {', '.join(deps.transitive) or 'none'}
- Callers: {', '.join(deps.callers) or 'none'}

Generate a structured investigation briefing in Markdown. Include these sections exactly:
1. ## Mission Summary (one paragraph)
2. ## Investigation Vectors (numbered list of 3-5 specific things to check)
3. ## Suggested Strategy (numbered steps)
4. ## Risk Assessment (brief: risk level, cross-module impact)
5. ## Testing Strategy (unit, integration, load if relevant)
6. ## Rollback Plan (one line)

Output ONLY the markdown, no preamble."""


async def generate_structure_8b(
    task: str,
    nav_result: NavResult,
    git_ctx: GitContext,
    deps: DepGraph,
) -> Tuple[str, float]:
    """Generate briefing structure with 8B model."""
    prompt = _format_structure_prompt(task, nav_result, git_ctx, deps)
    content, cost = await _call_groq(prompt, model="llama-3.1-8b-instant")
    return content.strip(), cost


async def enhance_with_70b(structure: str, task: str) -> Tuple[str, float]:
    """Enhance structure with 70B for deeper analysis."""
    prompt = f"""Task: {task}

Existing briefing structure:
{structure}

Enhance this briefing with more specific, actionable details. Keep the same section headers.
Add concrete line numbers, function names, or file references where helpful.
Output ONLY the enhanced markdown, no preamble."""
    content, cost = await _call_groq(
        prompt, model="llama-3.3-70b-versatile"
    )
    return content.strip(), cost


def generate_deep_prompt_section(
    brief: str,
    task: str,
    nav_result: NavResult,
    git_ctx: GitContext,
) -> str:
    """Generate 'Recommended Deep Model Prompt' section."""
    loc = f"{nav_result.target_file}:{nav_result.target_function}()"
    if nav_result.line_estimate:
        loc += f" lines {nav_result.line_estimate}"
    commit_ref = ""
    if git_ctx.last_commit_hash:
        commit_ref = f" Interaction with changes from commit {git_ctx.last_commit_hash}."
    return f'''

---

## 🤖 Recommended Deep Model Prompt

"Analyze the task: {task}. Focus on `{loc}`.{commit_ref}
Use the attached briefing context. Prioritize the Investigation Vectors. 
Reference the dependency map for impact scope."
'''


def generate_cost_section(
    scout_cost: float,
    complexity_score: float,
) -> str:
    """Generate cost comparison section."""
    naive_cost = ESTIMATED_EXPENSIVE_MODEL_COST
    savings = (1 - scout_cost / naive_cost) * 100 if naive_cost > 0 else 0
    return f'''

---

## 💰 Cost Efficiency

| Approach | Estimated Cost | Time |
|----------|---------------|------|
| **Naive deep model exploration** | ${naive_cost:.2f} | 4-5 minutes |
| **Scout + targeted deep model** | ${scout_cost + 0.15:.2f} | 45 seconds |
| **Savings** | **{savings:.1f}%** | **~5x faster** |

Scout uses Llama 8B for navigation and 70B only when complexity warrants.
Deep models (GPT-4, Opus, etc.) are reserved for final analysis, not exploration.
'''


def build_header(
    task: str,
    nav_result: NavResult,
    scout_cost: float,
    complexity_score: float,
) -> str:
    """Build briefing header."""
    gen_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    return f"""# Scout Briefing: {task}
Generated: {gen_time}
Scout Cost: ${scout_cost:.3f} (8B structure{f' + 70B enhancement' if complexity_score > COMPLEXITY_THRESHOLD else ''})
Estimated Expensive Model Cost Without Scout: ${ESTIMATED_EXPENSIVE_MODEL_COST:.2f}
**Savings: {(1 - scout_cost / ESTIMATED_EXPENSIVE_MODEL_COST) * 100:.1f}%**

---

"""


def build_target_section(nav_result: NavResult) -> str:
    """Build target location section."""
    return f"""## 📍 Target Location
**File:** `{nav_result.target_file}`
**Function:** `{nav_result.target_function}()` (lines {nav_result.line_estimate or '?'})
**Signature:** `{nav_result.signature or 'N/A'}`

"""


def build_change_context_section(git_ctx: GitContext) -> str:
    """Build change context section."""
    files_line = ", ".join(git_ctx.files_changed_together) or "none"
    return f"""## 📊 Change Context
- **Last Modified:** {git_ctx.last_modified} by @{git_ctx.last_author}
- **Commit:** `{git_ctx.last_commit_hash}` — "{git_ctx.last_commit_msg}"
- **Churn Score:** {git_ctx.churn_score}/10 (high activity, risky) 
- **Files Changed Together:** {files_line}

"""


def build_dependency_section(deps: DepGraph, git_ctx: GitContext) -> str:
    """Build dependency map section."""
    direct = "\n".join(f"- `{d}`" for d in deps.direct) or "- (none)"
    trans = "\n".join(f"- `{t}`" for t in deps.transitive) or "- (none)"
    return f"""## 🕸️ Dependency Map
**Direct Dependencies:**
{direct}

**Transitive Impact:**
{trans}

"""


def _resolve_pr_task(repo_root: Path, pr_number: int) -> str:
    """Resolve PR number to task title via gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "pr", "view", str(pr_number), "--json", "title"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return (data.get("title") or f"PR #{pr_number}").strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    return f"PR #{pr_number}"


async def get_navigation(
    task: str,
    entry: Optional[Path],
    repo_root: Path,
    config: ScoutConfig,
    audit: AuditLog,
    validator: Validator,
) -> Optional[NavResult]:
    """
    Navigate to entry point. Reuses scout-nav logic via TriggerRouter.
    """
    from vivarium.scout.router import TriggerRouter

    router = TriggerRouter(
        config=config,
        audit=audit,
        validator=validator,
        repo_root=repo_root,
    )
    result = await router.navigate_task(
        task=task,
        entry=entry,
    )
    if result is None:
        return None

    target_file = result.get("target_file", "")
    # Resolve directory/test targets to a suitable file for brief analysis
    resolved = _resolve_target_to_file(repo_root, target_file)
    if resolved is not None:
        target_file = resolved

    return NavResult(
        target_file=target_file,
        target_function=result.get("target_function", ""),
        line_estimate=result.get("line_estimate", 0) or 0,
        signature=result.get("signature", ""),
        cost=result.get("cost_usd", 0.0),
        session_id=result.get("session_id", _generate_session_id()),
        reasoning=result.get("reasoning", ""),
        suggestion=result.get("suggestion", ""),
        confidence=result.get("confidence", 0),
    )


async def generate_brief(
    task: str,
    entry: Optional[Path] = None,
    pr_number: Optional[int] = None,
    output_path: Optional[Path] = None,
) -> str:
    """
    Main flow: nav → git → deps → 8B structure → 70B if complex → deep prompt → cost.
    """
    repo_root = Path.cwd().resolve()
    config = ScoutConfig()
    audit = AuditLog()
    validator = Validator()

    # Resolve PR to task if needed
    if pr_number is not None:
        task = _resolve_pr_task(repo_root, pr_number)

    # 1. Navigate
    nav_result = await get_navigation(
        task, entry, repo_root, config, audit, validator
    )
    if nav_result is None:
        raise RuntimeError("Navigation failed or cost limit exceeded.")

    # 2. Git context
    git_ctx = gather_git_context(repo_root, nav_result.target_file)

    # 3. Dependencies
    deps = build_dependencies(repo_root, nav_result.target_file)

    # 4. Structure with 8B
    structure, cost_8b = await generate_structure_8b(
        task, nav_result, git_ctx, deps
    )
    audit.log("brief", session_id=nav_result.session_id, cost=cost_8b, model="llama-3.1-8b")

    total_cost = nav_result.cost + cost_8b

    # 5. Enhance with 70B if complex
    complexity_score = calculate_complexity(deps, git_ctx)
    if complexity_score > COMPLEXITY_THRESHOLD:
        enhanced, cost_70b = await enhance_with_70b(structure, task)
        structure = enhanced
        total_cost += cost_70b
        audit.log(
            "brief",
            session_id=nav_result.session_id,
            cost=cost_70b,
            model="llama-3.3-70b",
        )

    # 6. Add Recommended Deep Model Prompt
    deep_prompt = generate_deep_prompt_section(
        structure, task, nav_result, git_ctx
    )

    # 7. Cost section
    cost_section = generate_cost_section(total_cost, complexity_score)

    # Assemble
    header = build_header(task, nav_result, total_cost, complexity_score)
    target_sec = build_target_section(nav_result)
    change_sec = build_change_context_section(git_ctx)
    dep_sec = build_dependency_section(deps, git_ctx)

    brief = (
        header
        + target_sec
        + change_sec
        + dep_sec
        + structure
        + deep_prompt
        + cost_section
    )

    brief += f"\n---\n*Generated by Scout. Session ID: {nav_result.session_id}*\n"

    if output_path:
        output_path.write_text(brief, encoding="utf-8")

    return brief


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        prog="scout-brief",
        description="Scout: Generate Investigation Plans for expensive models",
    )
    parser.add_argument(
        "--task",
        metavar="TASK",
        help="Investigation task (e.g. 'fix race condition in token refresh')",
    )
    parser.add_argument(
        "--entry",
        metavar="PATH",
        help="Entry point hint (e.g. vivarium/runtime/auth/)",
    )
    parser.add_argument(
        "--pr",
        metavar="N",
        type=int,
        help="PR number (uses gh CLI if available to resolve task)",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Save briefing to file (default: stdout)",
    )
    return parser.parse_args()


async def _main_async(args: argparse.Namespace) -> int:
    """Async main entry."""
    repo_root = Path.cwd().resolve()
    if not (repo_root / "requirements.txt").exists():
        print("Error: Run from Vivarium repo root.", file=sys.stderr)
        return 1

    task = args.task
    if args.pr and not task:
        task = f"PR #{args.pr}"

    if not task:
        print("Error: --task or --pr required.", file=sys.stderr)
        return 1

    entry = Path(args.entry) if args.entry else None
    output_path = Path(args.output) if args.output else None

    try:
        brief = await generate_brief(
            task=task,
            entry=entry,
            pr_number=args.pr,
            output_path=output_path,
        )
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if not output_path:
        print(brief)

    return 0


def main() -> int:
    """Main entry point."""
    args = parse_args()
    return asyncio.run(_main_async(args))


if __name__ == "__main__":
    sys.exit(main())
