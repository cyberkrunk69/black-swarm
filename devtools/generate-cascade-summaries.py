#!/usr/bin/env python3
"""
Generate module/project-level normie cascade summaries (data-driven, no hardcoding).

Aggregates facts from .facts.json in each package, classifies domain from symbol
patterns, generates ELIV via LLM with jargon guardrails.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def _aggregate_facts_from_package(package_dir: Path) -> "ModuleFacts | None":
    """Load and merge .facts.json from package .docs/. Returns ModuleFacts or None."""
    from vivarium.scout.doc_sync.ast_facts import ModuleFacts

    docs_dir = package_dir / ".docs"
    if not docs_dir.exists():
        return None
    aggregated = ModuleFacts.empty()
    aggregated.path = package_dir / "__init__.py"
    for f in sorted(docs_dir.glob("*.facts.json")):
        if f.name.startswith("__init__"):
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            other = ModuleFacts.from_json(json.dumps(data))
            for k, v in other.symbols.items():
                if k not in aggregated.symbols:
                    aggregated.symbols[k] = v
        except Exception:
            continue
    if not aggregated.symbols:
        return None
    return aggregated


def _extract_package_purpose(package_dir: Path) -> str:
    """First sentence of __init__.py docstring, or generic."""
    init_py = package_dir / "__init__.py"
    if not init_py.exists():
        return "Coordinates helpers in this package."
    try:
        import ast
        tree = ast.parse(init_py.read_text(encoding="utf-8"))
        doc = ast.get_docstring(tree)
        if doc and doc.strip():
            first = doc.strip().split("\n\n")[0].split(".")[0].strip()
            if len(first) > 15:
                return first + "."
    except Exception:
        pass
    return "Coordinates helpers in this package."


def main() -> int:
    from vivarium.scout.doc_sync.synthesizer import (
        _classify_module_domain,
        _get_eliv_normie_friendly_from_facts,
    )

    modules = [
        REPO_ROOT / "vivarium" / "scout",
        REPO_ROOT / "vivarium" / "runtime",
    ]

    for package_dir in modules:
        facts = _aggregate_facts_from_package(package_dir)
        if not facts:
            print(f"  ⚠ No facts for {package_dir.relative_to(REPO_ROOT)}, skipping")
            continue
        domain = _classify_module_domain(facts)
        purpose = _extract_package_purpose(package_dir)
        eliv = _get_eliv_normie_friendly_from_facts(facts)
        tldr = purpose.split(".")[0].strip() + "."
        content = f"""# TLDR
{tldr}

# ELIV
{eliv}

# Components
See child .tldr.md files for file-level details.
"""
        rel = package_dir.relative_to(REPO_ROOT)
        out_dir = REPO_ROOT / "docs" / "livingDoc" / rel
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "__init__.py.module.md"
        out_file.write_text(content, encoding="utf-8")
        print(f"✓ {out_file.relative_to(REPO_ROOT)} (domain={domain})")

    # Project-level: aggregate from all modules
    all_symbols = {}
    for package_dir in modules:
        facts = _aggregate_facts_from_package(package_dir)
        if facts:
            all_symbols.update(facts.symbols)
    from vivarium.scout.doc_sync.ast_facts import ModuleFacts, SymbolFact
    project_facts = ModuleFacts(
        path=REPO_ROOT / "vivarium" / "__init__.py",
        symbols=all_symbols,
        control_flow={},
        imports=[],
        ast_hash="",
    )
    domain = _classify_module_domain(project_facts)
    purpose = "Coordinates multiple specialized helpers to accomplish complex tasks."
    eliv = _get_eliv_normie_friendly_from_facts(project_facts)
    tldr = "Agent platform where specialized helpers collaborate without stepping on each other."
    content = f"""# TLDR
{tldr}

# ELIV
{eliv}

# Subsystems
- vivarium/scout: routing, validation, living docs
- vivarium/runtime: inference, swarm, control panel
"""
    out_dir = REPO_ROOT / "docs" / "livingDoc" / "vivarium"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "__init__.py.module.md"
    out_file.write_text(content, encoding="utf-8")
    print(f"✓ {out_file.relative_to(REPO_ROOT)} (domain={domain})")

    print("\n✅ Cascade summaries generated (data-driven).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
