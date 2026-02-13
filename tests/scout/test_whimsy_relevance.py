"""
TICKET-31: Integration test — Whimsy reflects execution trace.

Verifies that gate whimsy mentions actual expanded symbols.
"""

from __future__ import annotations

import asyncio

from vivarium.scout.middle_manager import GateDecision
from vivarium.scout.ui.whimsy import (
    _fallback_gate_whimsy,
    _output_matches_facts,
    decision_to_whimsy_params,
    generate_gate_whimsy,
)


class TestWhimsyRelevance:
    """Whimsy must reflect actual execution facts."""

    def test_fallback_mentions_expanded_symbol(self):
        """Fallback includes expanded symbol when present."""
        out = _fallback_gate_whimsy(
            initial_conf=0.84,
            final_conf=0.84,
            expanded_symbols=["vivarium/runtime/resident_memory.py::serialize"],
            gaps=[],
            outcome="pass",
            cost_usd=0.05,
        )
        assert "resident_memory" in out.lower()

    def test_fallback_uses_first_expanded_when_multiple(self):
        """Fallback uses first expanded symbol."""
        out = _fallback_gate_whimsy(
            initial_conf=0.84,
            final_conf=0.84,
            expanded_symbols=[
                "vivarium/scout/audit.py::log",
                "vivarium/runtime/resident_memory.py::serialize",
            ],
            gaps=[],
            outcome="pass",
            cost_usd=0.05,
        )
        assert "audit" in out.lower()

    def test_output_matches_facts_rejects_hallucinated_symbol(self):
        """Reject output mentioning symbol not in expanded list."""
        # Output claims "safety.py::bar" but expanded only has "resident_memory.py::x"
        expanded = ["vivarium/runtime/resident_memory.py::serialize"]
        out_bad = "62% → safety.py::bar → 84% PASS"
        assert not _output_matches_facts(out_bad, 0.84, expanded)

    def test_output_matches_facts_accepts_actual_symbol(self):
        """Accept output with actual expanded symbol."""
        expanded = ["vivarium/runtime/resident_memory.py::serialize"]
        out_good = "62% → resident_memory.py → 84% PASS (5¢)"
        assert _output_matches_facts(out_good, 0.84, expanded)

    def test_output_matches_facts_requires_confidence(self):
        """Output must contain confidence number (±2% tolerance)."""
        assert not _output_matches_facts("Gate says PASS!", 0.84, [])
        assert _output_matches_facts("84% sure, PASS", 0.84, [])

    def test_decision_to_whimsy_params_includes_expanded_symbols(self):
        """decision_to_whimsy_params extracts expanded_symbols from GateDecision."""
        d = GateDecision(
            decision="pass",
            content="x",
            confidence=0.84,
            gaps=["impact on resident_memory.py::serialize"],
            source="compressed",
            attempt=1,
            expanded_symbols=["vivarium/runtime/resident_memory.py::serialize"],
        )
        params = decision_to_whimsy_params(d, cost_usd=0.05)
        assert "resident_memory" in str(params["expanded_symbols"]).lower()

    def test_generate_gate_whimsy_fallback_includes_symbol(self):
        """generate_gate_whimsy fallback (on mock failure) includes expanded symbol."""
        async def _fail(*args, **kwargs):
            raise RuntimeError("mock failure")

        out = asyncio.run(
            generate_gate_whimsy(
                initial_conf=0.62,
                final_conf=0.84,
                expanded_symbols=["vivarium/runtime/resident_memory.py::serialize"],
                gaps=["js adapters"],
                outcome="pass",
                cost_usd=0.05,
                llm_client=_fail,
            )
        )
        assert "resident_memory" in out.lower() or "context" in out.lower()
        assert "✨" in out


def test_hype_matches_facts_rejects_novel_for_low_tokens():
    """TICKET-30: Reject 'novel' when tokens < 500."""
    from vivarium.scout.ui.hype import _hype_matches_facts

    assert not _hype_matches_facts("Wrote a novel (10 tokens)", tokens_written=10)
    assert _hype_matches_facts("Wrote 600 tokens to middle_manager.py", tokens_written=600)
