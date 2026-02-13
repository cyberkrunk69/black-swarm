"""
TICKET-28: Outcome Hype Man — Post-action celebration.

One 8B call after workflow completion. Grounded in facts.
TICKET-30: Safety guardrails — factual grounding checks.
"""

from __future__ import annotations

from typing import Optional

MAX_HYPE_CHARS = 80
MIN_TOKENS_FOR_NOVEL = 500


def _hype_matches_facts(
    output: str,
    tokens_written: int,
    primary_file: str = "",
) -> bool:
    """
    TICKET-30: Reject hallucinated hype.
    - Reject "novel"/"book" for <500 tokens
    - Max 80 chars
    """
    if len(output) > MAX_HYPE_CHARS:
        return False
    if tokens_written < MIN_TOKENS_FOR_NOVEL:
        lower = output.lower()
        if "novel" in lower or "book" in lower:
            return False
    return True


def _fallback_outcome_hype(
    action: str,
    files_changed: int,
    tokens_written: int,
    primary_file: str = "",
) -> str:
    """Deterministic plain text fallback when 8B fails or hallucinates."""
    if action == "ship":
        return f"PR draft ready. {files_changed} file(s)."
    if action == "doc_sync":
        return f"Wrote {tokens_written} tokens to {files_changed} file(s)."
    if action == "query":
        return f"Query complete. {tokens_written} chars."
    return f"Done. {action}"


async def generate_outcome_hype(
    action: str,
    files_changed: int,
    tokens_written: int,
    confidence: Optional[float] = None,
    gaps_declared: int = 0,
    primary_file: str = "",
    llm_client=None,
) -> str:
    """
    TICKET-28: One 8B call after workflow completion — hype grounded in actual output.
    Fallback to deterministic plain text if 8B fails or hallucinates.
    """
    conf_str = f", {int((confidence or 0) * 100)}% conf" if confidence is not None else ""
    prompt = f"""Write ONE line (<80 chars) celebrating this dev workflow outcome. Use emoji. Be creative but FACTUAL.

FACTS (use these exactly):
- action: {action}
- files_changed: {files_changed}
- tokens_written: {tokens_written}{conf_str}
- gaps_declared: {gaps_declared}
- primary_file: {primary_file or "none"}

Rules: Do NOT say "novel" or "book" if tokens < 500. One line only."""

    try:
        from vivarium.scout.llm import call_groq_async

        resp = await call_groq_async(
            prompt,
            model="llama-3.1-8b-instant",
            system="You output exactly one short celebratory line. No explanation. Max 80 chars.",
            max_tokens=64,
            llm_client=llm_client,
        )
        out = (resp.content or "").strip()
        if len(out) > MAX_HYPE_CHARS:
            out = out[: MAX_HYPE_CHARS - 1].rstrip() + "…"
        if _hype_matches_facts(out, tokens_written, primary_file):
            return f"✨ {out}"
        return f"✨ {_fallback_outcome_hype(action, files_changed, tokens_written, primary_file)}"
    except Exception:
        return f"✨ {_fallback_outcome_hype(action, files_changed, tokens_written, primary_file)}"
