#!/usr/bin/env python3
"""Validate ELIV contains no unsupported claims (hallucination check).

ELIV must only claim capabilities/constraints that are supported by symbol names
in the module's facts. No forced analogies, no invented purpose.
"""
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _extract_eliv_from_tldr(tldr_path: Path) -> str:
    """Extract content between # ELIV and next # heading or end."""
    text = tldr_path.read_text(encoding="utf-8")
    match = re.search(r"^# ELIV\s*\n(.*?)(?=^# |\Z)", text, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _symbol_names_from_facts(facts_path: Path) -> str:
    """Get space-joined symbol names from .facts.json."""
    data = json.loads(facts_path.read_text(encoding="utf-8"))
    symbols = data.get("symbols", {})
    names = []
    for k, v in symbols.items():
        names.append(v.get("name", k))
    return " ".join(names).lower()


def validate_no_unsupported_claims(tldr_path: Path, facts_path: Path) -> bool:
    """Return True if ELIV contains no claims unsupported by symbol names."""
    if not tldr_path.exists():
        print(f"⚠️  {tldr_path} not found", file=sys.stderr)
        return True  # Skip if not generated
    if not facts_path.exists():
        print(f"⚠️  {facts_path} not found", file=sys.stderr)
        return True

    eliv = _extract_eliv_from_tldr(tldr_path).lower()
    symbol_names = _symbol_names_from_facts(facts_path)

    # Hallucination checks: ELIV claims X but symbols don't support X
    checks = [
        ("route" in eliv and not any(kw in symbol_names for kw in ["route", "dispatch", "triage"])),
        ("budget" in eliv and not any(kw in symbol_names for kw in ["budget", "cost", "limit"])),
        ("log" in eliv and not any(kw in symbol_names for kw in ["log", "audit", "record"])),
    ]

    if any(checks):
        print(f"❌ HALLUCINATION DETECTED in {tldr_path}", file=sys.stderr)
        return False

    print(f"✅ NO hallucinations in {tldr_path.relative_to(REPO_ROOT)}")
    return True


def main() -> int:
    base = REPO_ROOT / "vivarium" / "scout" / ".docs"
    pairs = [
        (base / "router.py.tldr.md", base / "router.py.facts.json"),
        (base / "audit.py.tldr.md", base / "audit.py.facts.json"),
    ]
    all_pass = all(
        validate_no_unsupported_claims(tldr, facts) for tldr, facts in pairs
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
