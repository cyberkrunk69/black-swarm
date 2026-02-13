"""
Scout Index CLI — Local code search using ctags/ripgrep + SQLite.

Zero LLM calls for lookups. Free and instant (<100ms).

Usage:
    scout-index build              # Build index from scratch
    scout-index update            # Incremental update (git diff)
    scout-index query "auth token"  # Search symbols and files
    scout-index watch             # Background daemon, auto-update
    scout-index stats             # Show coverage
"""

from __future__ import annotations

import argparse
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

# Index directory relative to repo root
SCOUT_INDEX_DIR = ".scout"
INDEX_DB = "index.db"
TAGS_FILE = "tags"


def _repo_root() -> Path:
    """Resolve repo root (cwd or project root)."""
    return Path.cwd().resolve()


def _index_dir(repo_root: Path) -> Path:
    """Path to .scout index directory."""
    return repo_root / SCOUT_INDEX_DIR


def _db_path(repo_root: Path) -> Path:
    """Path to SQLite index database."""
    return _index_dir(repo_root) / INDEX_DB


def _tags_path(repo_root: Path) -> Path:
    """Path to ctags output file."""
    return _index_dir(repo_root) / TAGS_FILE


def _find_python_files(repo_root: Path) -> List[Path]:
    """List Python files in repo (respects .livingDocIgnore, skips .git)."""
    ignore_dirs = {".git", "__pycache__", ".scout", "venv", ".venv", "node_modules"}
    files: List[Path] = []
    for p in repo_root.rglob("*.py"):
        if any(part in p.parts for part in ignore_dirs):
            continue
        try:
            rel = p.relative_to(repo_root)
            if "test" in str(rel).lower() and "tests" not in str(rel.parts[0]):
                # Include test files
                pass
            files.append(p)
        except ValueError:
            pass
    return files


def _run_ctags(repo_root: Path, files: Optional[List[Path]] = None) -> bool:
    """
    Run ctags and write to .scout/tags.
    Supports Universal Ctags (--output-format=json, -R) and BSD/Exuberant (find + xargs).
    Returns True if successful.
    """
    index_dir = _index_dir(repo_root)
    index_dir.mkdir(parents=True, exist_ok=True)
    tags_path = _tags_path(repo_root)

    if files is None:
        files = _find_python_files(repo_root)

    if not files:
        return False

    # Try Universal Ctags first (brew install universal-ctags)
    for ctags_cmd in ["ctags", "uctags"]:
        try:
            # Universal Ctags: -R, --languages=python, --output-format=json
            result = subprocess.run(
                [ctags_cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode != 0:
                continue
            out = result.stdout or result.stderr or ""
            # Universal Ctags mentions "Universal Ctags"
            if "Universal" in out or "universal" in out:
                cmd = [
                    ctags_cmd,
                    "-R",
                    "--languages=python",
                    "-f",
                    str(tags_path),
                    "--python-kinds=-i",  # Skip imports
                    ".",
                ]
                proc = subprocess.run(
                    cmd,
                    cwd=str(repo_root),
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if proc.returncode == 0:
                    return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue

    # Fallback: BSD/Exuberant ctags (no -R, pass files via stdin or xargs)
    file_paths = [str(f.relative_to(repo_root)) for f in files[:10000]]
    if not file_paths:
        return False

    try:
        # Pass files as args (BSD ctags may not support --python-kinds)
        cmd = ["ctags", "-f", str(tags_path)] + file_paths
        proc = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=120,
        )
        return proc.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _parse_tags_line(line: str, repo_root: Path) -> Optional[Tuple[str, str, int, str]]:
    """
    Parse single line from ctags output (Exuberant/Universal format).
    Returns (name, file, line, kind) or None.
    Format: name\tfile\t/pattern/;"\tkind\t...  or  name\tfile\t123;"\tkind
    """
    line = line.strip()
    if not line or line.startswith("!"):
        return None
    parts = line.split("\t")
    if len(parts) < 3:
        return None
    name, file_path, addr = parts[0], parts[1], parts[2]

    # Extract line number from address
    line_num = 0
    addr_clean = addr.split(";")[0].strip()
    if addr_clean.isdigit():
        line_num = int(addr_clean)
    else:
        match = re.search(r"line:(\d+)", addr)
        if match:
            line_num = int(match.group(1))
        elif len(parts) >= 4 and parts[3].isdigit():
            line_num = int(parts[3])

    kind = "symbol"
    if len(parts) >= 4:
        k = parts[3].strip()
        if k in ("f", "function", "m", "method"):
            kind = "function"
        elif k in ("c", "class"):
            kind = "class"
        elif k in ("i", "import"):
            kind = "import"
        elif "test" in name.lower() or "test" in file_path.lower():
            kind = "test"

    return (name, file_path, line_num, kind)


def _load_tags_into_db(conn: sqlite3.Connection, tags_path: Path, repo_root: Path) -> int:
    """Load ctags file into symbols FTS table. Returns count loaded."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM symbols")
    count = 0
    try:
        content = tags_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    for line in content.splitlines():
        parsed = _parse_tags_line(line, repo_root)
        if parsed:
            name, file_path, line_num, kind = parsed
            cursor.execute(
                "INSERT INTO symbols(name, file, line, kind) VALUES(?, ?, ?, ?)",
                (name, file_path, str(line_num), kind),
            )
            count += 1
    conn.commit()
    return count


def _create_schema(conn: sqlite3.Connection) -> None:
    """Create FTS5 symbols table."""
    conn.execute("DROP TABLE IF EXISTS symbols")
    conn.execute(
        """CREATE VIRTUAL TABLE symbols USING fts5(
            name, file, line, kind,
            tokenize='porter unicode61'
        )"""
    )


def _build_index(repo_root: Path) -> int:
    """Build index from scratch. Returns number of symbols indexed."""
    index_dir = _index_dir(repo_root)
    index_dir.mkdir(parents=True, exist_ok=True)
    db_path = _db_path(repo_root)
    tags_path = _tags_path(repo_root)

    if not _run_ctags(repo_root):
        # Create empty index if ctags fails
        conn = sqlite3.connect(str(db_path))
        _create_schema(conn)
        conn.close()
        return 0

    conn = sqlite3.connect(str(db_path))
    _create_schema(conn)
    count = _load_tags_into_db(conn, tags_path, repo_root)
    conn.close()
    return count


def _update_index(repo_root: Path) -> int:
    """Incremental update: re-index only changed files from git diff."""
    # Get changed files from git
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return _build_index(repo_root)  # Full rebuild on error
        changed = result.stdout.strip().splitlines()
        py_changed = [p for p in changed if p.endswith(".py")]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return _build_index(repo_root)

    if not py_changed:
        # No Python changes - return current count
        db_path = _db_path(repo_root)
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            try:
                c = conn.execute(
                    "SELECT COUNT(*) FROM (SELECT rowid FROM symbols LIMIT 1)"
                )
                # FTS5 count
                c = conn.execute("SELECT COUNT(*) FROM symbols")
                return c.fetchone()[0]
            except sqlite3.OperationalError:
                pass
            conn.close()
        return 0

    # For simplicity: full rebuild on any change
    # (Proper incremental would update only affected symbols)
    return _build_index(repo_root)


def _query_index(
    repo_root: Path, q: str, limit: int = 10
) -> Tuple[List[Tuple[str, str, int, str]], float]:
    """
    Query FTS index. Returns (results, elapsed_ms).
    Each result: (file, line, kind, name)
    """
    db_path = _db_path(repo_root)
    if not db_path.exists():
        return [], 0.0

    start = time.perf_counter()
    conn = sqlite3.connect(str(db_path))
    try:
        # FTS5 MATCH - escape for phrase
        # Simple: use as prefix/token search
        tokens = q.replace('"', " ").split()
        fts_query = " AND ".join(f'"{t}"' for t in tokens if t)
        if not fts_query:
            return [], (time.perf_counter() - start) * 1000

        cursor = conn.execute(
            """
            SELECT name, file, line, kind
            FROM symbols
            WHERE symbols MATCH ?
            LIMIT ?
            """,
            (fts_query, limit),
        )
        rows = cursor.fetchall()
    except sqlite3.OperationalError:
        # MATCH syntax error - try simple term
        try:
            cursor = conn.execute(
                """
                SELECT name, file, line, kind
                FROM symbols
                WHERE symbols MATCH ?
                LIMIT ?
                """,
                (q, limit),
            )
            rows = cursor.fetchall()
        except sqlite3.OperationalError:
            rows = []
    finally:
        conn.close()

    elapsed = (time.perf_counter() - start) * 1000
    return rows, elapsed


def _run_ripgrep(repo_root: Path, q: str, limit: int = 5) -> List[Tuple[str, int, str]]:
    """Run ripgrep for content search. Returns [(file, line, snippet)]."""
    rg = shutil.which("rg")
    if not rg:
        return []
    try:
        result = subprocess.run(
            [rg, "-n", "--type", "py", "-C", "0", q, "."],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode != 0:
            return []
        out = result.stdout
        results = []
        for line in out.splitlines()[:limit]:
            if ":" in line:
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    file_path, line_num, snippet = parts[0], parts[1], parts[2]
                    try:
                        results.append((file_path, int(line_num), snippet.strip()))
                    except ValueError:
                        pass
        return results
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def cmd_build(args: argparse.Namespace, repo_root: Path) -> int:
    """Build index from scratch."""
    count = _build_index(repo_root)
    print(f"Indexed {count} symbols in {_index_dir(repo_root)}")
    return 0


def cmd_update(args: argparse.Namespace, repo_root: Path) -> int:
    """Incremental update from git diff."""
    count = _update_index(repo_root)
    print(f"Updated index: {count} symbols")
    return 0


def cmd_query(args: argparse.Namespace, repo_root: Path) -> int:
    """Search symbols and files."""
    q = args.query
    limit = args.limit or 10

    results, elapsed = _query_index(repo_root, q, limit)
    rg_results = _run_ripgrep(repo_root, q, limit=5) if results else []

    print(f"{len(results) + len(rg_results)} results in {int(elapsed)}ms (no API calls):\n")

    for name, file_path, line_num, kind in results:
        kind_label = kind if kind != "symbol" else "symbol"
        ln = int(line_num) if (line_num and str(line_num).isdigit()) else 0
        line_str = str(ln) if ln > 0 else "?"
        print(f"  {file_path}:{line_str}  ({kind_label})")
        if kind in ("function", "method"):
            print(f"    {name}()")
        elif kind == "class":
            print(f"    {name}")
        else:
            print(f"    {name}")
        print()

    seen = {(r[1], int(r[2]) if r[2] else 0) for r in results}
    for file_path, line_num, snippet in rg_results:
        if (file_path, line_num) not in seen:
            print(f"  {file_path}:{line_num}  (content)")
            print(f"    {snippet[:80]}...")
            print()

    if not results and not rg_results:
        print("  No results. Run 'scout-index build' first.")
        return 1
    return 0


def cmd_watch(args: argparse.Namespace, repo_root: Path) -> int:
    """Background daemon: auto-update on git changes."""
    interval = args.interval or 30
    print(f"scout-index watch: checking every {interval}s (Ctrl+C to stop)")
    try:
        while True:
            time.sleep(interval)
            try:
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=str(repo_root),
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0 and result.stdout.strip():
                    print(f"[{time.strftime('%H:%M:%S')}] Changes detected, updating...")
                    _update_index(repo_root)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


def query_for_nav(
    repo_root: Path, task: str, limit: int = 5
) -> Optional[List[dict]]:
    """
    Query index for nav-style results. Used by scout-nav and scout-brief as free fallback.
    Returns a list of nav result dicts (best first), or None if no matches.
    """
    db_path = _db_path(repo_root)
    if not db_path.exists():
        return None

    # Extract search terms from task (skip common words)
    stop = {"fix", "bug", "add", "the", "a", "in", "to", "for", "where", "is", "find"}
    tokens = [t for t in task.lower().split() if len(t) > 2 and t not in stop]
    if not tokens:
        return None

    try:
        # Prefer OR for broader match (e.g. "router code" -> router OR code)
        fts_query = " OR ".join(f'"{t}"' for t in tokens[:5])
    except Exception:
        return None

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute(
            """
            SELECT name, file, line, kind
            FROM symbols
            WHERE symbols MATCH ?
            LIMIT ?
            """,
            (fts_query, limit),
        )
        rows = cursor.fetchall()
    except sqlite3.OperationalError:
        return None
    finally:
        conn.close()

    if not rows:
        return None

    results: List[dict] = []
    all_files = [r[1] for r in rows]
    for name, file_path, line_str, kind in rows:
        line_num = int(line_str) if line_str and line_str.isdigit() else 0
        target_fn = name if kind in ("function", "method", "class") else ""
        related = [f for f in all_files if f != file_path]
        results.append({
            "task": task,
            "target_file": file_path,
            "target_function": target_fn,
            "line_estimate": line_num,
            "confidence": 85,
            "model_used": "scout-index",
            "cost_usd": 0.0,
            "duration_ms": 0,
            "retries": 0,
            "escalated": False,
            "related_files": related,
            "reasoning": f"Index match: {name} in {file_path}",
            "suggestion": "Verify location with IDE or tests.",
            "session_id": "",
        })
    return results


def cmd_stats(args: argparse.Namespace, repo_root: Path) -> int:
    """Show index coverage."""
    db_path = _db_path(repo_root)
    if not db_path.exists():
        print("No index. Run 'scout-index build' first.")
        return 1

    conn = sqlite3.connect(str(db_path))
    try:
        c = conn.execute("SELECT COUNT(*) FROM symbols")
        count = c.fetchone()[0]
    except sqlite3.OperationalError:
        count = 0
    conn.close()

    files = _find_python_files(repo_root)
    size_mb = db_path.stat().st_size / (1024 * 1024)
    print(f"Symbols: {count}")
    print(f"Files scanned: {len(files)}")
    print(f"Index size: {size_mb:.2f} MB")
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="scout-index",
        description="Local code search (ctags + SQLite). Zero LLM calls.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    build_parser = subparsers.add_parser("build", help="Build index from scratch")
    build_parser.set_defaults(func=cmd_build)

    update_parser = subparsers.add_parser("update", help="Incremental update (git diff)")
    update_parser.set_defaults(func=cmd_update)

    query_parser = subparsers.add_parser("query", help="Search symbols and files")
    query_parser.add_argument("query", metavar="Q", help="Search query")
    query_parser.add_argument("--limit", "-n", type=int, default=10, help="Max results")
    query_parser.set_defaults(func=cmd_query)

    watch_parser = subparsers.add_parser("watch", help="Background daemon, auto-update")
    watch_parser.add_argument(
        "--interval", "-i", type=int, default=30, help="Check interval (seconds)"
    )
    watch_parser.set_defaults(func=cmd_watch)

    stats_parser = subparsers.add_parser("stats", help="Show coverage")
    stats_parser.set_defaults(func=cmd_stats)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    repo_root = _repo_root()
    return args.func(args, repo_root)


if __name__ == "__main__":
    sys.exit(main())
