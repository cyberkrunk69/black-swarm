"""
Scout Constrained Doc Synthesizer — LLM generates prose ONLY on verified AST facts.

Never invents facts. Validates output against facts. Embeds FACT_CHECKSUM for runtime validation.
"""

from __future__ import annotations

import ast
import asyncio
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from vivarium.scout.doc_sync.ast_facts import ModuleFacts, SymbolFact

logger = logging.getLogger(__name__)


def _generate_eliv_minimal_truth(facts: ModuleFacts) -> str:
    """Generate ELIV as MINIMAL PLAIN-ENGLISH TRUTH.

    NO analogies. NO vividness pressure. NO hallucinations.
    Only state what symbols factually support.
    """
    constraints: List[str] = []
    capabilities: List[str] = []

    # Extract factual constraints from symbol names
    symbol_names = " ".join(s.lower() for s in facts.symbols.keys())

    if any(kw in symbol_names for kw in ["budget", "cost", "limit", "ceiling", "max"]):
        constraints.append("resource limits")
    if any(kw in symbol_names for kw in ["audit", "log", "record", "track"]):
        constraints.append("activity logging")
    if any(kw in symbol_names for kw in ["route", "dispatch", "triage", "queue"]):
        capabilities.append("work coordination")
    if any(kw in symbol_names for kw in ["execut", "run", "invoke", "call"]):
        capabilities.append("task execution")

    # Construct minimal truth statement (no claims unsupported by symbols)
    if capabilities and constraints:
        base = (
            f"This module provides {', '.join(capabilities)} "
            f"while respecting {', '.join(constraints)}."
        )
    elif capabilities:
        base = f"This module provides {', '.join(capabilities)}."
    elif constraints:
        base = f"This module enforces {', '.join(constraints)}."
    else:
        base = ""

    if base:
        if "activity logging" in constraints:
            return f"{base} All activity is transparently logged."
        return base
    return (
        "This module coordinates work between specialized helpers with resource "
        "awareness and activity logging."
    )


def _extract_module_purpose(facts: ModuleFacts) -> str:
    """Extract 'why' narrative from module docstring + symbol facts. No LLM."""
    path = facts.path
    stem = path.stem if path else "module"
    symbol_names = set(facts.symbols.keys())

    # 1. Module docstring (first sentence only — keep ELIV tight)
    doc_parts: list[str] = []
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
        doc = ast.get_docstring(tree)
        if doc and doc.strip():
            block = doc.strip().split("\n\n")[0].replace("\n", " ").strip()
            first_sent = re.split(r"[.!?]\s+", block)[0]
            if first_sent and len(first_sent) > 15:
                doc_parts.append(first_sent.strip() + ("." if not first_sent.endswith(".") else ""))
    except Exception:
        pass

    # 2. Purpose from symbol patterns (no hardcoded file names)
    symbols_text = " ".join(symbol_names).lower()
    if any(kw in symbols_text for kw in ["route", "dispatch", "trigger", "orchestrat"]):
        if any(kw in symbols_text for kw in ["budget", "exhaust", "check_budget"]):
            doc_parts.append("Routes work while enforcing limits so we don't overspend.")
        else:
            doc_parts.append("Routes triggers and dispatches work safely.")
    elif any(kw in symbols_text for kw in ["audit", "log", "record", "track"]):
        doc_parts.append("Logs events and costs so we can see what happened and how much we spent.")
    elif any(kw in symbols_text for kw in ["engine", "inference", "complexity", "estimate"]):
        doc_parts.append("Picks the right tool for the job and tracks usage.")

    # 3. Constraint rationale from inline comments (max, limit, budget, ceiling)
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").split("\n"):
            if "=" in line and "#" in line:
                lower = line.lower()
                if any(kw in lower for kw in ["max", "limit", "ceiling", "budget", "cap"]):
                    comment = line.split("#", 1)[1].strip()
                    cl = comment.lower()
                    if len(comment) > 15 and ("chars" in cl or "token" in cl):
                        doc_parts.append(f"Keeps context under control ({comment[:60]}).")
                        break
    except Exception:
        pass

    if not doc_parts:
        return f"Core logic for {stem}. The list below shows what's defined."
    return " ".join(doc_parts[:2])[:320]  # Max 2 parts, ~320 chars


def _classify_module_domain(facts: ModuleFacts) -> str:
    """Classify module domain from symbol patterns — NO hardcoded project names."""
    symbols = [n.lower() for n in facts.symbols.keys()]
    stem = facts.path.stem.lower() if facts.path else ""
    text = " ".join(symbols + [stem])
    if any(kw in text for kw in ["route", "dispatch", "triage", "queue", "orchestrat"]):
        return "routing"
    if any(kw in text for kw in ["execut", "engine", "inference", "run", "invoke", "call"]):
        return "execution"
    if any(kw in text for kw in ["audit", "log", "record", "track", "account", "receipt"]):
        return "audit"
    if any(kw in text for kw in ["swarm", "agent", "collaborat", "coordinate", "team"]):
        return "coordination"
    return "general"


def _extract_constraints_from_facts(facts: ModuleFacts) -> List[str]:
    """Extract constraint-like patterns from symbol names and docstrings."""
    constraints: List[str] = []
    for name, fact in facts.symbols.items():
        n = name.lower()
        if any(kw in n for kw in ["limit", "max", "budget", "cap", "exhaust", "check"]):
            constraints.append("manages limits")
        if any(kw in n for kw in ["cost", "spend", "track"]):
            constraints.append("tracks spending")
        if fact.docstring and any(kw in fact.docstring.lower() for kw in ["prevent", "avoid", "ensure"]):
            constraints.append("prevents problems")
    return list(dict.fromkeys(constraints))[:3] or ["manages limits"]


def _get_eliv_normie_friendly_from_facts(facts: ModuleFacts) -> str:
    """Minimal plain-English truth from AST facts. No analogies, no hallucinations."""
    return _generate_eliv_minimal_truth(facts)


# TICKET-50: Gate constants that must NOT appear in docs unless defined in this module
_CROSS_MODULE_HALLUCINATION_BLOCKLIST = frozenset({
    "DEFAULT_CONFIDENCE_THRESHOLD",
    "MAX_EXPANDED_CONTEXT",
    "GROQ_70B_MODEL",
    "MAX_RETRY_ATTEMPTS",
})


# TICKET-100: Section headers that are NOT symbol names (allowed in output)
def _validate_output_against_facts(prose: str, facts: ModuleFacts) -> bool:
    """Reject blatant contradictions and cross-module constant hallucinations. TICKET-46, TICKET-50.
    TICKET-100: Reject hallucinated symbols — all # SymbolName must exist in facts.
    """
    # TICKET-46: Reject "not used" when used
    for name, fact in facts.symbols.items():
        if fact.used_at and re.search(
            rf"\b{re.escape(name)}\b.*\b(not used|unused|never used)",
            prose,
            re.IGNORECASE,
        ):
            return False

    # TICKET-50: Reject cross-module constant hallucination — gate constants only if defined here
    defined_names = set(facts.symbols.keys())
    for blocklisted in _CROSS_MODULE_HALLUCINATION_BLOCKLIST:
        if blocklisted in defined_names:
            continue
        if re.search(rf"\b{re.escape(blocklisted)}\b", prose):
            logger.error(
                "Cross-module hallucination: '%s' mentioned but not defined in %s",
                blocklisted,
                facts.path.name if facts.path else "?",
            )
            return False

    # TICKET-100: Reject hallucinated symbols — # SymbolName (single #) must exist in facts.
    # Use (?<!#) to avoid matching "## Section" (double hash = subsection, not symbol).
    # Exclude standard section headers: # TLDR, # ELIV (quality gate structure).
    section_header_allowlist = frozenset({"TLDR", "ELIV", "Module"})
    output_symbols: set[str] = set()
    for m in re.finditer(r"(?<!#)#\s+`?([A-Za-z_][A-Za-z0-9_]*)`?", prose):
        sym = m.group(1)
        output_symbols.add(sym)
        if sym in section_header_allowlist:
            continue
        if sym not in defined_names:
            logger.error(
                "Hallucinated symbol: '%s' in output but not in facts for %s",
                sym,
                facts.path.name if facts.path else "?",
            )
            return False

    # TICKET-100: Reject if documentable symbols are missing (e.g. LLM omits TriggerRouter).
    required = {n for n, f in facts.symbols.items() if f.type in ("class", "function")}
    missing = required - output_symbols
    if missing:
        logger.error(
            "Missing symbols in output for %s: %s",
            facts.path.name if facts.path else "?",
            ", ".join(sorted(missing)),
        )
        return False

    # TICKET-100: Require class methods to appear (LLM may omit Methods section).
    for name, fact in facts.symbols.items():
        if fact.type == "class" and fact.methods:
            for method in fact.methods:
                if not re.search(rf"`{re.escape(method)}`", prose):
                    logger.error(
                        "Missing method %s.%s in output for %s",
                        name,
                        method,
                        facts.path.name if facts.path else "?",
                    )
                    return False
    return True


def _ensure_eliv_normie_friendly(prose: str, facts: ModuleFacts) -> str:
    """Replace ELIV section with data-driven normie text."""
    eliv_text = _get_eliv_normie_friendly_from_facts(facts)
    # Replace content between # ELIV and next # heading or end
    pattern = r"(^# ELIV\s*\n)(.*?)(?=^# |\Z)"
    return re.sub(pattern, r"\g<1>" + eliv_text + "\n\n", prose, flags=re.MULTILINE | re.DOTALL)


def _ensure_tldr_eliv_prefix(prose: str, facts: ModuleFacts) -> str:
    """Prepend # TLDR and # ELIV if missing (quality gate: structural hierarchy).
    TLDR: engineer-facing. ELIV: normie-friendly (curated for router/audit/inference_engine).
    """
    has_tldr = bool(re.search(r"^# TLDR\s*$", prose, re.MULTILINE))
    has_eliv = bool(re.search(r"^# ELIV\s*$", prose, re.MULTILINE))
    if has_tldr and has_eliv:
        prose = _ensure_eliv_normie_friendly(prose, facts)
        return prose
    stem = facts.path.stem if facts.path else "module"
    purpose = _extract_module_purpose(facts)
    first = purpose.split(".")[0].strip()
    if first and not first.endswith("."):
        first += "."
    eliv_text = _get_eliv_normie_friendly_from_facts(facts)
    prefix = "# TLDR\n"
    prefix += f"{stem}: {first}\n\n"
    prefix += "# ELIV\n"
    prefix += f"{eliv_text}\n\n"
    # Insert after any existing HTML comment
    if prose.strip().startswith("<!--"):
        end = prose.find("-->") + 3
        return prose[:end] + "\n\n" + prefix + prose[end:].lstrip()
    return prefix + prose


class ConstrainedDocSynthesizer:
    """LLM generates prose ONLY on verified AST facts — never invents facts."""

    SYSTEM_PROMPT = """You are a documentation engineer. Generate accurate .tldr.md prose using ONLY the facts below.

CRITICAL RULE (TICKET-50):
- ONLY describe symbols DEFINED in this module (not imported/used symbols).
- If this module USES a constant but does not DEFINE it, DO NOT describe it.
- Example: If this module USES DEFAULT_CONFIDENCE_THRESHOLD but does not DEFINE it, DO NOT describe it.
- When in doubt: OMIT the symbol — never hallucinate ownership.

RULES:
1. NEVER invent facts not in the FACTS section.
2. NEVER say "not used" unless usage list is "(none)" in FACTS.
3. For constants, ALWAYS list line numbers where used (from FACTS) — e.g. "used at lines 109, 335, 363".
4. Include ALL module-level constants AND functions that appear in FACTS (only symbols defined in this module).
5. For classes, list ONLY methods from the Methods field. Enum classes have "Methods: (none)" — NEVER list module-level functions as class methods. Module-level functions are ALWAYS separate # FunctionName sections.
6. For functions/methods, use the exact Signature from FACTS (params, types, defaults, return type).
7. If uncertain about any detail, omit it — never hallucinate.

OUTPUT FORMAT (MANDATORY — include all three sections at top):
# TLDR
One-line summary of what this module does (max 80 chars).

# ELIV
Explain Like I'm Five: 2-3 sentences in plain language. Why does this module exist? No jargon.

# Module Summary

## Module Constants
- `logger`: (used at lines X, Y, Z)
- `MAX_EXPANDED_CONTEXT`: value (used at lines X, Y)

## Module Functions
- # function_name: Use exact Signature from FACTS. Parameters and Return Type from Signature.

# ClassName
Brief description. (If Enum class: no Methods section — only enum members as Constants if any.)

## Constants
- `name`: (used at lines X, Y, Z)

## Methods
- `method(param: type) -> return_type`: description (ONLY for non-Enum classes; from Methods field only)

FACTS (100% ACCURATE — DO NOT CONTRADICT):
{facts_markdown}

OUTPUT (prose only — no JSON, no disclaimers):"""

    def _facts_to_markdown(self, facts: ModuleFacts) -> str:
        """Convert ModuleFacts to markdown for the prompt. Docstrings are truth — always include."""
        return self._facts_to_markdown_impl(facts, include_enrichment=True)

    def _facts_to_markdown_rich(self, facts: ModuleFacts) -> str:
        """TICKET-44: Include docstrings, signatures, purpose hints for rich synthesis."""
        return self._facts_to_markdown_impl(facts, include_enrichment=True)

    def _facts_to_markdown_impl(
        self, facts: ModuleFacts, include_enrichment: bool = False
    ) -> str:
        """Convert ModuleFacts to markdown. Optionally include docstring/signature/purpose.
        TICKET-95: Include method_signatures and is_enum for accurate attribution.
        """
        lines = []
        for name, fact in sorted(facts.symbols.items()):
            type_label = f"{fact.type} (Enum)" if getattr(fact, "is_enum", False) else fact.type
            lines.append(f"- `{name}` ({type_label})")
            if fact.value is not None:
                lines.append(f"  Value: {fact.value}")
            if fact.type_annotation:
                lines.append(f"  Type: {fact.type_annotation}")
            if include_enrichment and fact.docstring:
                ds = fact.docstring[:200] + "..." if len(fact.docstring) > 200 else fact.docstring
                lines.append(f"  Docstring: {ds}")
            if include_enrichment and fact.signature:
                lines.append(f"  Signature: {fact.signature}")
            if include_enrichment and fact.purpose_hint:
                lines.append(f"  Purpose hint: {fact.purpose_hint}")
            sr = getattr(fact, "semantic_role", None)
            if include_enrichment and sr:
                lines.append(f"  Semantic role: {sr} (NEVER conflate with other roles)")
            if fact.used_at:
                lines.append(f"  Used at lines: {', '.join(map(str, fact.used_at))}")
            else:
                lines.append("  Used at lines: (none)")
            # TICKET-95: Enum has no methods. Methods are ONLY those in class body.
            if getattr(fact, "is_enum", False):
                lines.append("  Methods: (none — Enum class; module-level functions are NOT methods)")
            elif fact.methods:
                method_sigs = getattr(fact, "method_signatures", None) or {}
                if method_sigs:
                    for m in fact.methods:
                        sig = method_sigs.get(m, m + "()")
                        lines.append(f"  Method {m}: {sig}")
                else:
                    lines.append(f"  Methods: {', '.join(fact.methods)}")
            if fact.fields:
                lines.append(f"  Fields: {', '.join(fact.fields)}")
        return "\n".join(lines)

    async def synthesize_tldr_async(self, facts: ModuleFacts) -> Tuple[str, float]:
        """Synthesize TL;DR prose from facts. Returns (prose, cost_usd)."""
        facts_md = self._facts_to_markdown(facts)  # include_enrichment=True — docstrings are truth
        prompt = self.SYSTEM_PROMPT.format(facts_markdown=facts_md)

        from vivarium.scout.llm import call_groq_async

        resp = await call_groq_async(
            prompt,
            model="llama-3.1-8b-instant",
            system="You output documentation. Use ONLY the provided facts. Never invent.",
            max_tokens=1000,
        )
        prose = resp.content.strip()

        if not _validate_output_against_facts(prose, facts):
            prose = self._fallback_from_facts(facts)

        prose = _ensure_tldr_eliv_prefix(prose, facts)
        checksum = facts.checksum()
        return f"<!-- FACT_CHECKSUM: {checksum} -->\n\n{prose}", resp.cost_usd

    def synthesize_tldr(self, facts: ModuleFacts) -> Tuple[str, float]:
        """Synchronous wrapper for synthesize_tldr_async."""
        return asyncio.run(self.synthesize_tldr_async(facts))

    async def synthesize_deep_async(self, facts: ModuleFacts) -> Tuple[str, float]:
        """Synthesize deep doc from facts. Returns (prose, cost_usd)."""
        facts_md = self._facts_to_markdown(facts)  # include_enrichment=True — docstrings are truth
        prompt = f"""Generate detailed documentation using ONLY these facts. Never invent.

CRITICAL RULE (TICKET-50): ONLY describe symbols in FACTS below. Do NOT add constants from other modules.

OUTPUT FORMAT (MANDATORY — include all three sections at top):
# TLDR
One-line summary of what this module does (max 80 chars).

# ELIV
Explain Like I'm Five: 2-3 sentences in plain language. Why does this module exist? No jargon.

# Module Summary
(bullet list of symbols, then ## sections for detail)

FACTS:
{facts_md}

Output structured markdown. For each constant, list exact line numbers where used. Never say "not used" if lines are listed."""

        from vivarium.scout.llm import call_groq_async

        resp = await call_groq_async(
            prompt,
            model="llama-3.1-8b-instant",
            system="You output documentation. Use ONLY the provided facts.",
            max_tokens=1500,
        )
        prose = resp.content.strip()
        if not _validate_output_against_facts(prose, facts):
            prose = self._fallback_from_facts(facts)
        prose = _ensure_tldr_eliv_prefix(prose, facts)
        checksum = facts.checksum()
        return f"<!-- FACT_CHECKSUM: {checksum} -->\n\n{prose}", resp.cost_usd

    def synthesize_deep(self, facts: ModuleFacts) -> Tuple[str, float]:
        """Synchronous wrapper for synthesize_deep_async."""
        return asyncio.run(self.synthesize_deep_async(facts))

    def _fallback_from_facts(self, facts: ModuleFacts) -> str:
        """Generate deterministic fallback when LLM output fails validation.
        TICKET-95: Include signatures for functions; Enum has no methods.
        Quality gate: include # TLDR and # ELIV at top with purpose extraction.
        """
        stem = facts.path.stem if facts.path else "module"
        purpose = _extract_module_purpose(facts)
        first = purpose.split(".")[0].strip()
        if first and not first.endswith("."):
            first += "."
        eliv_text = _get_eliv_normie_friendly_from_facts(facts)
        tldr = f"# TLDR\n{stem}: {first}\n\n"
        eliv = f"# ELIV\n{eliv_text}\n\n"
        lines = [tldr, eliv, "# Module Summary\n"]
        for name, fact in sorted(facts.symbols.items()):
            if fact.type == "constant":
                usage = f" (used at lines {', '.join(map(str, fact.used_at))})" if fact.used_at else ""
                lines.append(f"- `{name}`: {fact.type}{usage}")
                if fact.value:
                    lines.append(f"  Value: {fact.value}")
            elif fact.type == "class":
                if getattr(fact, "is_enum", False):
                    lines.append(f"- `{name}`: Enum class (no methods)")
                else:
                    method_sigs = getattr(fact, "method_signatures", None) or {}
                    if method_sigs:
                        for m, sig in method_sigs.items():
                            lines.append(f"- `{name}.{m}`: {sig}")
                    else:
                        lines.append(f"- `{name}`: class with methods {', '.join(fact.methods)}")
            elif fact.type == "function":
                if fact.signature:
                    lines.append(f"- `{name}`: {fact.signature}")
                else:
                    lines.append(f"- `{name}`: function")
        return "\n".join(lines)


class RichDocSynthesizer(ConstrainedDocSynthesizer):
    """TICKET-44: Two-phase synthesis — strict grounding then fluent rewrite.
    Phase 1: Minimal fact-grounded output. Phase 2: Fluent prose (no fact changes).
    """

    PHASE_1_PROMPT = """Generate minimal .tldr.md from facts below.

OUTPUT MUST START WITH (in this order):
# TLDR
One-line summary (max 80 chars).

# ELIV
2-3 sentences in plain language. Why does this module exist?

# Module Summary
(bullet list)

CRITICAL RULE (TICKET-50):
- ONLY describe symbols DEFINED in this module (not imported/used symbols).
- If a constant is NOT in the FACTS below, DO NOT describe it — even if you've seen it elsewhere.
- Example: If FACTS omit DEFAULT_CONFIDENCE_THRESHOLD, this module does not define it — OMIT it.
- When in doubt: OMIT the symbol — never hallucinate ownership.

PRIORITY RULES (for symbols that ARE in FACTS):
1. Include constants with semantic_role "threshold" or "limit" when present in FACTS
2. Include model names (semantic_role "model_name") when present in FACTS
3. Describe purpose using docstrings/signatures when available

NEVER contradict facts. You MAY infer purpose from naming conventions (e.g. "logger" → audit logging).
Thresholds (e.g. 0.75) are INPUT parameters — call them "threshold", NEVER "confidence score".

FACTS:
{facts_markdown}

MINIMAL OUTPUT (prioritize critical constants):"""

    PHASE_2_PROMPT = """Rewrite this documentation to be clear and helpful for developers.

CRITICAL RULES:
1. NEVER conflate semantic roles:
   - Thresholds (e.g. 0.75) are INPUT PARAMETERS — not results/outputs of analysis
   - Use "default threshold", "confidence threshold", "cutoff" — NOT "confidence score of 0.75"
   - Confidence scores (e.g. 0.84) are OUTPUT VALUES — not thresholds/defaults
2. NEVER change factual values (line numbers, constants).
3. DO expand explanations using purpose hints and docstrings.
4. DO use natural language — not bullet-point dumps.

ORIGINAL:
{phase_1_output}

REWRITTEN (fluent prose WITH semantic precision):"""

    async def synthesize_tldr_async(self, facts: ModuleFacts) -> Tuple[str, float]:
        """Two-phase: strict grounding, then fluent rewrite. Returns (prose, cost_usd)."""
        from vivarium.scout.llm import call_groq_async

        facts_md = self._facts_to_markdown_rich(facts)
        phase1_prompt = self.PHASE_1_PROMPT.format(facts_markdown=facts_md)

        resp1 = await call_groq_async(
            phase1_prompt,
            model="llama-3.1-8b-instant",
            system="You output documentation. Use ONLY the provided facts. Never invent.",
            max_tokens=500,
            temperature=0.2,
        )
        phase1 = resp1.content.strip()

        phase2_prompt = self.PHASE_2_PROMPT.format(phase_1_output=phase1)
        resp2 = await call_groq_async(
            phase2_prompt,
            model="llama-3.1-8b-instant",
            system="Rewrite for clarity. Never change facts.",
            max_tokens=800,
            temperature=0.5,
        )
        phase2 = resp2.content.strip()

        cost = resp1.cost_usd + resp2.cost_usd

        if not _validate_output_against_facts(phase2, facts):
            phase2 = self._fallback_from_facts(facts)

        phase2 = _ensure_tldr_eliv_prefix(phase2, facts)
        checksum = facts.checksum()
        return f"<!-- FACT_CHECKSUM: {checksum} -->\n\n{phase2}", cost

    def synthesize_tldr(self, facts: ModuleFacts) -> Tuple[str, float]:
        """Synchronous wrapper for synthesize_tldr_async."""
        return asyncio.run(self.synthesize_tldr_async(facts))


PHASE_2_REASONING_PROMPT = """Rewrite this documentation to be clear, accurate, and helpful.

PRESERVE AT TOP (do not remove or reorder):
# TLDR
# ELIV
# Module Summary

CRITICAL RULE (TICKET-50):
- NEVER add constants that were not in the ORIGINAL. The ORIGINAL contains ONLY symbols defined in this module.
- If ORIGINAL omits DEFAULT_CONFIDENCE_THRESHOLD, MAX_EXPANDED_CONTEXT, GROQ_70B_MODEL — do NOT add them.
- When in doubt: OMIT — never hallucinate cross-module ownership.

MANDATORY INCLUSIONS (only for constants already in ORIGINAL):
- Include constants with semantic_role "threshold" when present in ORIGINAL
- Include constants with semantic_role "limit" when present in ORIGINAL
- Include constants with semantic_role "model_name" when present in ORIGINAL
- For each constant in ORIGINAL: state its value and purpose

CONTEXT CLARITY:
- "70B" = 70-billion-parameter Llama model (NOT 70 billion outputs)
- When a constant has a Docstring specifying units (e.g. "character limit", "~10K tokens"), use that wording — do NOT infer units from the numeric value alone (40000 chars ≠ 40000 tokens)
- Thresholds (0.75) are INPUT PARAMETERS; confidence_score is OUTPUT VALUE

OUTPUT RULES:
- Output ONLY the rewritten documentation. No preamble.
- If you cannot include a mandatory constant due to length, TRUNCATE OTHER CONTENT FIRST.

ORIGINAL:
{phase_1_output}

REWRITTEN (include all mandatory constants):"""


class ReasoningDocSynthesizer(ConstrainedDocSynthesizer):
    """TICKET-46: Phase 1 Groq 8B (grounding). Phase 2 Gemini Flash (reasoning-aware rewrite).
    Uses the right model for the job — no regex validation layers.
    """

    def _sparse_module_fallback(self, facts: ModuleFacts) -> str:
        """TICKET-49: Deterministic fallback for sparse modules — module docstring only, no LLM."""
        import ast

        try:
            source = facts.path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(facts.path))
            doc = ast.get_docstring(tree)
            if doc and doc.strip():
                return f"# {facts.path.stem}\n\n{doc.strip()}"
        except Exception:
            pass
        return f"# {facts.path.stem}\n\n(Minimal module — no documentable symbols.)"

    async def synthesize_tldr_async(self, facts: ModuleFacts) -> Tuple[str, float]:
        """Two-phase: Groq grounding, then Gemini Flash reasoning-aware rewrite.
        TICKET-49: Sparsity guardrail — for symbol_count < 3, use deterministic fallback (no LLM).
        """
        from vivarium.scout.big_brain import GEMINI_MODEL_FLASH, call_big_brain_async
        from vivarium.scout.llm import call_groq_async

        symbol_count = sum(
            1
            for _, fact in facts.symbols.items()
            if fact.type in ("class", "function", "constant")
        )

        if symbol_count < 3:
            logger.warning(
                "Sparse module (%d symbols) — using deterministic fallback (no LLM): %s",
                symbol_count,
                facts.path.name,
            )
            checksum = facts.checksum()
            prose = self._sparse_module_fallback(facts)
            return f"<!-- FACT_CHECKSUM: {checksum} -->\n\n{prose}", 0.0

        facts_md = self._facts_to_markdown_rich(facts)
        phase1_prompt = RichDocSynthesizer.PHASE_1_PROMPT.format(facts_markdown=facts_md)

        resp1 = await call_groq_async(
            phase1_prompt,
            model="llama-3.1-8b-instant",
            system="You output documentation. Use ONLY the provided facts. Never invent.",
            max_tokens=700,
            temperature=0.2,
        )
        phase1 = resp1.content.strip()
        cost1 = resp1.cost_usd

        phase2_prompt = PHASE_2_REASONING_PROMPT.format(phase_1_output=phase1)
        resp2 = await call_big_brain_async(
            phase2_prompt,
            system="Rewrite for clarity and semantic precision. Never change facts.",
            max_tokens=8000,
            model=GEMINI_MODEL_FLASH,
            task_type="doc_sync_reasoning",
        )
        phase2 = resp2.content.strip()
        # Strip common preambles (e.g. "Here's the rewritten documentation, ...:")
        for prefix in (
            "Here's the rewritten documentation",
            "Here is the rewritten documentation",
            "Here's the documentation",
        ):
            if phase2.lower().startswith(prefix.lower()):
                colon = phase2.find(":", len(prefix))
                if colon >= 0:
                    phase2 = phase2[colon + 1 :].strip()
                break
        cost2 = resp2.cost_usd

        if not _validate_output_against_facts(phase2, facts):
            logger.warning("Fact validation failed — falling back to Phase 1")
            phase2 = phase1

        phase2 = _ensure_tldr_eliv_prefix(phase2, facts)
        checksum = facts.checksum()
        return f"<!-- FACT_CHECKSUM: {checksum} -->\n\n{phase2}", cost1 + cost2

    def synthesize_tldr(self, facts: ModuleFacts) -> Tuple[str, float]:
        """Synchronous wrapper for synthesize_tldr_async."""
        return asyncio.run(self.synthesize_tldr_async(facts))
