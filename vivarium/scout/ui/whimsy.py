"""
TICKET-20/21/27: Whimsy Layer — Gate + Outcome Delight

TICKET-27: Per-query gate whimsy via 8B — fresh, execution-grounded.
TICKET-30: Safety guardrails — factual grounding checks.
"""

from __future__ import annotations

import re
from typing import List, Literal, Optional

from vivarium.scout.middle_manager import GateDecision

# TICKET-27: 8B model for whimsy (~$0.00002/query)
WHIMSY_MODEL = "llama-3.1-8b-instant"
MAX_WHIMSY_CHARS = 80
CONFIDENCE_TOLERANCE = 2  # ±2% for factual grounding

# Regex to extract path::symbol from gap text (same as middle_manager)
_SYMBOL_FROM_GAP_RE = re.compile(r"(\S+\.py)::(\w+)")


def _extract_symbols_from_gaps(gaps: List[str]) -> List[str]:
    """Extract path::symbol refs from gap text."""
    result: List[str] = []
    for gap in gaps:
        for m in _SYMBOL_FROM_GAP_RE.finditer(gap):
            try:
                path_str, symbol_name = m.group(1), m.group(2)
                result.append(f"{path_str}::{symbol_name}")
            except (ValueError, IndexError):
                continue
    return list(dict.fromkeys(result))


def _output_matches_facts(
    output: str,
    confidence: float,
    expanded: List[str],
    tokens: int = 0,
) -> bool:
    """
    TICKET-30: Reject hallucinated whimsy.
    - Confidence number must be present (±2% tolerance)
    - Must not mention symbols not in expanded list
    - Must not claim "novel"/"book" for <500 tokens
    - Max 80 chars
    """
    if len(output) > MAX_WHIMSY_CHARS:
        return False
    conf_pct = int(confidence * 100)
    # Check confidence appears (allow ±2%)
    if str(conf_pct) not in output:
        # Try adjacent values
        found = any(str(c) in output for c in range(conf_pct - 2, conf_pct + 3))
        if not found:
            return False
    # Reject "novel"/"book" for <500 tokens
    if tokens > 0 and tokens < 500:
        lower = output.lower()
        if "novel" in lower or "book" in lower:
            return False
    # Reject mentions of symbols not in expanded (hallucination)
    for match in _SYMBOL_FROM_GAP_RE.finditer(output):
        ref = match.group(0)
        if expanded and ref not in expanded:
            # Allow partial match (e.g. "resident_memory" when expanded has "resident_memory.py::x")
            path_part = ref.split("::")[0].replace(".py", "")
            if not any(path_part in e for e in expanded):
                return False
    return True


def _format_cost(cost_usd: float) -> str:
    """TICKET-40/48: Exact cost — never round, never hardcode."""
    if cost_usd < 0.01:
        return f"${cost_usd:.4f}"
    if cost_usd < 1.0:
        return f"${cost_usd:.2f}"
    return f"${cost_usd:.2f}"


def _fallback_gate_whimsy(
    initial_conf: float,
    final_conf: float,
    expanded_symbols: List[str],
    gaps: List[str],
    outcome: Literal["pass", "escalate", "reject"],
    cost_usd: float,
) -> str:
    """TICKET-48a: Execution-grounded format — all values from gate decision."""
    conf_emoji = "🤨" if initial_conf < 0.70 else "😐" if initial_conf < 0.85 else "😎"
    outcome_emoji = (
        "😎 PASS" if outcome == "pass" else "🚨 ESCALATE" if outcome == "escalate" else "❌ REJECT"
    )
    expansion = ""
    if expanded_symbols:
        display_syms = [s.split("::")[0] if "::" in s else s for s in expanded_symbols[:2]]
        expansion = f" → 👯 {' + '.join(display_syms)}"
    delta = final_conf - initial_conf
    delta_display = f" → 📈 +{int(delta * 100)}%" if delta > 0.05 else ""
    cost_display = _format_cost(cost_usd)
    return f"✨ {conf_emoji} {int(initial_conf * 100)}%{expansion}{delta_display} → {outcome_emoji} ({cost_display})"


async def generate_gate_whimsy(
    initial_conf: float,
    final_conf: float,
    expanded_symbols: List[str],
    gaps: List[str],
    outcome: str,
    cost_usd: float,
    llm_client=None,
) -> str:
    """
    TICKET-27: One 8B call per gate decision — fresh whimsy grounded in execution facts.
    Fallback to deterministic plain text if 8B fails or hallucinates.
    """
    conf_pct = int(final_conf * 100)
    delta = int((final_conf - initial_conf) * 100) if initial_conf != final_conf else 0
    syms_str = ", ".join(expanded_symbols[:3]) if expanded_symbols else "none"
    gaps_str = "; ".join(gaps[:2]) if gaps else "none"
    cost_str = _format_cost(cost_usd)

    prompt = f"""Write ONE line (<80 chars) celebrating this gate decision. Use emoji. Be creative but FACTUAL.

FACTS (use these exactly):
- confidence: {conf_pct}%
- delta: +{delta}% (from {int(initial_conf*100)}%)
- expanded: {syms_str}
- gaps: {gaps_str}
- outcome: {outcome}
- cost: {cost_str}

Rules: Include the actual confidence number. Mention only symbols from expanded list. No hallucination. One line only."""

    try:
        from vivarium.scout.llm import call_groq_async

        resp = await call_groq_async(
            prompt,
            model=WHIMSY_MODEL,
            system="You output exactly one short celebratory line. No explanation. Max 80 chars.",
            max_tokens=64,
            llm_client=llm_client,
        )
        out = (resp.content or "").strip()
        if len(out) > MAX_WHIMSY_CHARS:
            out = out[: MAX_WHIMSY_CHARS - 1].rstrip() + "…"
        if _output_matches_facts(out, final_conf, expanded_symbols):
            return f"✨ {out}"
        return f"✨ {_fallback_gate_whimsy(initial_conf, final_conf, expanded_symbols, gaps, outcome, cost_usd)}"
    except Exception:
        return f"✨ {_fallback_gate_whimsy(initial_conf, final_conf, expanded_symbols, gaps, outcome, cost_usd)}"


def decision_to_whimsy_params(decision: GateDecision, cost_usd: float) -> dict:
    """Map GateDecision to generate_gate_whimsy params."""
    expanded = decision.expanded_symbols or _extract_symbols_from_gaps(decision.gaps)
    conf = decision.confidence or 0.0
    initial = decision.initial_confidence if hasattr(decision, "initial_confidence") else conf
    return {
        "initial_conf": initial or conf,
        "final_conf": conf,
        "expanded_symbols": expanded,
        "gaps": decision.gaps,
        "outcome": (
            "pass"
            if decision.decision == "pass"
            else "reject"
            if decision.decision == "reject"
            else "escalate"
        ),
        "cost_usd": cost_usd,
    }


# --- Legacy WhimsyFormatter (TICKET-21) — kept for SCOUT_WHIMSY=0 or fallback ---
from vivarium.scout.ui.whimsy_data import DEFAULT_PHRASE_BANKS, load_user_phrase_bank
import hashlib
from typing import Any, Dict


def _pick(
    seed: str,
    banks: Dict[str, Any],
    bank_key: str,
    subkey: Optional[str] = None,
) -> str:
    """Deterministic rotation: hash(seed + key) % len(bank)."""
    bank = banks.get(bank_key, [])
    if subkey is not None and isinstance(bank, dict):
        bank = bank.get(subkey, [])
    if not bank or not isinstance(bank, list):
        return "???"
    salt = f"{bank_key}:{subkey or ''}"
    idx = int(hashlib.md5((seed + salt).encode()).hexdigest(), 16) % len(bank)
    return bank[idx]


class WhimsyFormatter:
    """Legacy phrase-bank formatter. Use generate_gate_whimsy when SCOUT_WHIMSY=1."""

    CONFIDENCE_FACE = [
        ((0.0, 0.6), "🤨 Meh"),
        ((0.6, 0.8), "🤔 Pretty sure"),
        ((0.8, 1.01), "😎 Confident (not lying!)"),
    ]

    @classmethod
    def format_gate_decision(
        cls,
        decision: GateDecision,
        *,
        use_emoji: bool = True,
        query: str = "",
    ) -> str:
        """Legacy: format gate decision with phrase banks."""
        seed = query or "default"
        banks: Dict[str, Any] = {**DEFAULT_PHRASE_BANKS, **load_user_phrase_bank()}
        if decision.decision == "pass":
            return cls._format_pass(decision, use_emoji, seed, banks)
        return cls._format_escalate(decision, use_emoji, seed, banks)

    @classmethod
    def _format_pass(
        cls,
        decision: GateDecision,
        use_emoji: bool,
        seed: str,
        banks: Dict[str, Any],
    ) -> str:
        door = "🚪" if use_emoji else "[Gate]"
        role = _pick(seed, banks, "roles", "gatekeeper")
        verb = _pick(seed, banks, "pass_verbs")
        cost = _pick(seed, banks, "cost_phrases", "flash")
        face = f" {cls._confidence_face(decision.confidence)}" if use_emoji else ""
        conf_pct = int((decision.confidence or 0) * 100)
        if decision.gaps:
            q = "❓" if use_emoji else "?"
            prefix = _pick(seed, banks, "gap_prefixes")
            gaps = "\n   ".join(f"{q} {prefix} {g}" for g in decision.gaps)
        else:
            gaps = "✅ No gaps!" if use_emoji else "No gaps!"
        spark = "💡 " if use_emoji else ""
        brain = f"Bright Spark ({cost})"
        return f"""{door} {role} says: "{verb}"{face}
   Confidence: {conf_pct}% sure (not lying!)
   {gaps}
   {spark}Sending to {brain}"""

    @classmethod
    def _format_escalate(
        cls,
        decision: GateDecision,
        use_emoji: bool,
        seed: str,
        banks: Dict[str, Any],
    ) -> str:
        door = "🚪" if use_emoji else "[Gate]"
        role = _pick(seed, banks, "roles", "gatekeeper")
        boss = _pick(seed, banks, "roles", "boss")
        cost_pro = _pick(seed, banks, "cost_phrases", "pro")
        boss_prefix = "👔 " if use_emoji else ""
        warn = "⚠️  " if use_emoji else ""
        if decision.attempt == 0:
            reason = _pick(seed, banks, "escalate_reasons", "stale")
            milk = " 🥛" if use_emoji else ""
            return f"""{door} {role} says: "Nah fam, this {reason}"{milk}
   Reason: cache expired (stale)
   {boss_prefix}Calling {boss} ({cost_pro}) — worth it for wisdom
   {warn}Warning: This query costs 10x more — worth it?"""
        reason = _pick(seed, banks, "escalate_reasons", "low_confidence")
        conf_pct = int((decision.confidence or 0) * 100)
        shook = " 😰" if use_emoji else ""
        return f"""{door} {role} says: "{reason}"{shook}
   Confidence: {conf_pct}% — too low!
   {boss_prefix}Escalating to {boss} ({cost_pro}) for deep wisdom"""

    @classmethod
    def _confidence_face(cls, conf: Optional[float]) -> str:
        if conf is None:
            return "🤨 Meh"
        for (low, high), face in cls.CONFIDENCE_FACE:
            if low <= conf < high:
                return face
        return "🤨 Meh"
