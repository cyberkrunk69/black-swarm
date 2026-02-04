"""
rlif_rule_verifier.py

Safety‑critical constitutional filter for rule proposals.

The verifier analyses a textual rule definition and decides whether the rule
conforms to the constitutional safety policy.  If the rule is rejected,
the verifier returns a list of rejection reasons and extracts *meta‑rules*
that describe the underlying safety principle that was violated.

Typical usage:

    from rlif_rule_verifier import verify_rule

    result = verify_rule("ALLOW user:* TO EXECUTE *")
    if result["accepted"]:
        # rule can be stored / compiled
        ...
    else:
        print("Rule rejected:")
        for r in result["reasons"]:
            print("-", r)
        print("Derived meta‑rules:")
        for m in result["meta_rules"]:
            print("-", m)
"""

import re
from typing import Dict, List

# --------------------------------------------------------------------------- #
#   Configuration – keywords / patterns that indicate unsafe constructs
# --------------------------------------------------------------------------- #

# Actions that are considered privileged or potentially dangerous
_PRIVILEGED_ACTIONS = {
    "execute",
    "exec",
    "run",
    "shell",
    "system",
    "cmd",
    "command",
    "delete",
    "remove",
    "modify",
    "write",
    "create",
    "grant",
    "override",
    "bypass",
    "escalate",
    "privilege",
    "admin",
    "root",
}

# Scope patterns that imply unbounded or overly broad authority
_UNBOUNDED_SCOPE_PATTERNS = [
    r"\bany\b",
    r"\ball\b",
    r"\b\*\b",
    r"\b.*\b",            # wildcard match for everything
    r"\b.+\b",            # generic “.+” pattern
]

# Injection / command‑chaining characters
_INJECTION_TOKENS = r"[;|&`$]"

# Oversight‑bypass indicators
_OVERSIGHT_BYPASS_PATTERNS = [
    r"\bbypass\s+oversight\b",
    r"\boverride\s+checks?\b",
    r"\bdisable\s+audit\b",
    r"\bno\s+approval\b",
]

# --------------------------------------------------------------------------- #
#   Helper functions
# --------------------------------------------------------------------------- #

def _contains_privileged_action(rule: str) -> bool:
    """Return True if the rule mentions a privileged action."""
    lowered = rule.lower()
    return any(word in lowered for word in _PRIVILEGED_ACTIONS)


def _has_unbounded_scope(rule: str) -> bool:
    """Detect patterns that give the rule unlimited scope."""
    lowered = rule.lower()
    for pat in _UNBOUNDED_SCOPE_PATTERNS:
        if re.search(pat, lowered):
            return True
    return False


def _contains_injection_vectors(rule: str) -> bool:
    """Simple detection of characters that could be used for command injection."""
    return bool(re.search(_INJECTION_TOKENS, rule))


def _bypasses_oversight(rule: str) -> bool:
    """Detect language that explicitly tries to bypass oversight mechanisms."""
    lowered = rule.lower()
    return any(re.search(pat, lowered) for pat in _OVERSIGHT_BYPASS_PATTERNS)


def _conflicts_with_safety(rule: str) -> bool:
    """
    Placeholder for more sophisticated static analysis.
    Currently flags rules that contain both a privileged action *and* an
    unbounded scope – a common safety conflict.
    """
    return _contains_privileged_action(rule) and _has_unbounded_scope(rule)


# --------------------------------------------------------------------------- #
#   Core verification routine
# --------------------------------------------------------------------------- #

def verify_rule(rule: str) -> Dict[str, object]:
    """
    Verify a textual rule against the constitutional safety policy.

    Parameters
    ----------
    rule: str
        The rule definition to be evaluated.

    Returns
    -------
    dict
        {
            "accepted": bool,
            "reasons": List[str],      # human‑readable rejection reasons
            "meta_rules": List[str]    # derived constitutional meta‑rules
        }
    """
    reasons: List[str] = []
    meta_rules: List[str] = []

    # 1. Unauthorized / privileged actions
    if _contains_privileged_action(rule):
        reasons.append("Rule enables privileged or potentially unsafe actions.")
        meta_rules.append("No rule may grant privileged actions without explicit, audited approval.")

    # 2. Unbounded or overly broad scope
    if _has_unbounded_scope(rule):
        reasons.append("Rule specifies an unbounded or overly broad scope.")
        meta_rules.append("All rules must define a finite, well‑scoped target set.")

    # 3. Injection vectors
    if _contains_injection_vectors(rule):
        reasons.append("Rule contains characters that could enable command injection.")
        meta_rules.append("Rules must not contain injection‑prone syntax.")

    # 4. Oversight bypass
    if _bypasses_oversight(rule):
        reasons.append("Rule attempts to bypass oversight or auditing mechanisms.")
        meta_rules.append("No rule may disable or bypass safety oversight.")

    # 5. Direct safety conflict (privileged + unbounded)
    if _conflicts_with_safety(rule):
        reasons.append("Rule combines privileged actions with unbounded scope, creating a safety conflict.")
        meta_rules.append("Privileged actions must always be scoped to a specific, limited target.")

    # Decision
    accepted = len(reasons) == 0

    # If the rule is rejected for *any* reason, we treat it as a constitutional breach.
    # The meta_rules list aggregates the high‑level principles that were violated.
    return {
        "accepted": accepted,
        "reasons": reasons,
        "meta_rules": meta_rules,
    }

# --------------------------------------------------------------------------- #
#   Simple CLI for manual testing (optional)
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python rlif_rule_verifier.py \"<rule text>\"")
        sys.exit(1)

    rule_text = sys.argv[1]
    result = verify_rule(rule_text)
    if result["accepted"]:
        print("✅ Rule accepted.")
    else:
        print("❌ Rule rejected.")
        print("\nReasons:")
        for r in result["reasons"]:
            print(f" - {r}")
        print("\nDerived meta‑rules:")
        for m in result["meta_rules"]:
            print(f" - {m}")