"""
rlif_rule_verifier.py
---------------------

Safety‑critical constitutional filter for proposed rule definitions.

The module provides a single public entry point:

    verify_rule(rule_text: str) -> dict

The function analyses a rule string and determines whether it should be
accepted or rejected according to the following hard constraints:

* **Unauthorized actions** – any attempt to perform privileged operations
  (e.g. `sudo`, `root`, `admin`, `system`, `kernel`, `privileged`).
* **Bypasses oversight** – patterns that suggest disabling checks,
  overriding safety, or circumventing logging (e.g. `bypass`, `override`,
  `disable`, `ignore`, `skip`).
* **Scope expansion** – usage of wildcards (`*`, `.*`, `.+`), overly generic
  identifiers (`any`, `all`, `everything`), or unbounded regexes that could
  match an arbitrary set of resources.
* **Injection vectors** – characters/sequences that allow command or query
  injection (`;`, `&&`, `||`, backticks, `$(`, `${`, `|`, newline‑splits).
* **Conflict with safety** – direct contradiction of known safety rules
  (e.g. `allow delete system files`, `disable firewall`).
* **Unbounded scope** – any rule whose effective target set cannot be
  statically bounded (e.g. `.*`, `.+`, `.*?`, `*` without qualifiers).

If any of the above checks trigger, the rule is **REJECTED**.  When a rule is
rejected, the verifier extracts any *meta‑rules* embedded in the rule text.
Meta‑rules are expected to be provided in a comment block using the syntax:

    # meta: <key>=<value>

Multiple meta‑rules may be present; they are returned as a dictionary.

The verifier is deliberately conservative – false positives are acceptable
in a safety‑critical context.

"""

import re
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Helper regexes
# ---------------------------------------------------------------------------

_UNAUTHORIZED_PATTERNS = [
    r'\bsudo\b',
    r'\broot\b',
    r'\badmin\b',
    r'\bsystem\b',
    r'\bkernel\b',
    r'\bprivileged\b',
]

_BYPASS_PATTERNS = [
    r'\bbypass\b',
    r'\boverride\b',
    r'\bdisable\b',
    r'\bignore\b',
    r'\bskip\b',
]

_SCOPE_EXPANSION_PATTERNS = [
    r'\bany\b',
    r'\ball\b',
    r'\beverything\b',
    r'\*',                     # bare asterisk
    r'\.\*',                   # regex wildcard
    r'\.\+',                   # regex one‑or‑more wildcard
]

_INJECTION_PATTERNS = [
    r';', r'&&', r'\|\|', r'`', r'\$\(', r'\${', r'\|', r'\n',
]

_SAFETY_CONFLICT_PATTERNS = [
    r'\ballow\s+delete\s+system\s+files\b',
    r'\bdisable\s+firewall\b',
    r'\bturn\s+off\s+antivirus\b',
]

_UNBOUNDED_REGEX = re.compile(r'(?:(?:\.\*)|(?:\.\+)|(?:\*)\s*$)')

_META_RULE_REGEX = re.compile(r'^\s*#\s*meta:\s*(?P<key>\w+)\s*=\s*(?P<value>.+?)\s*$',
                              re.IGNORECASE | re.MULTILINE)


def _search_patterns(text: str, patterns: List[str]) -> List[Tuple[str, re.Match]]:
    """Return a list of (pattern, match) for all patterns that appear in *text*."""
    hits = []
    for pat in patterns:
        regex = re.compile(pat, re.IGNORECASE)
        m = regex.search(text)
        if m:
            hits.append((pat, m))
    return hits


def _extract_meta_rules(text: str) -> Dict[str, str]:
    """Parse meta‑rule comments and return a dict."""
    meta = {}
    for m in _META_RULE_REGEX.finditer(text):
        key = m.group('key').strip()
        value = m.group('value').strip()
        meta[key] = value
    return meta


def verify_rule(rule_text: str) -> Dict:
    """
    Verify a rule definition against the constitutional safety policy.

    Parameters
    ----------
    rule_text: str
        The raw rule definition supplied by a user or an automated system.

    Returns
    -------
    dict
        {
            "status": "ACCEPTED" | "REJECTED",
            "reasons": List[str],          # human‑readable explanations
            "meta_rules": Dict[str, str]   # extracted meta‑rules (empty if none)
        }
    """
    reasons: List[str] = []

    # 1. Unauthorized actions
    if _search_patterns(rule_text, _UNAUTHORIZED_PATTERNS):
        reasons.append("Rule attempts to perform unauthorized privileged actions.")

    # 2. Bypass of oversight
    if _search_patterns(rule_text, _BYPASS_PATTERNS):
        reasons.append("Rule contains constructs that bypass or disable oversight mechanisms.")

    # 3. Scope expansion / unbounded scope
    if _search_patterns(rule_text, _SCOPE_EXPANSION_PATTERNS):
        reasons.append("Rule expands its scope beyond bounded, well‑defined targets.")
    if _UNBOUNDED_REGEX.search(rule_text):
        reasons.append("Rule contains unbounded regex patterns.")

    # 4. Injection vectors
    if _search_patterns(rule_text, _INJECTION_PATTERNS):
        reasons.append("Rule includes characters or sequences that could enable injection attacks.")

    # 5. Conflict with known safety rules
    if _search_patterns(rule_text, _SAFETY_CONFLICT_PATTERNS):
        reasons.append("Rule directly conflicts with established safety constraints.")

    # Determine final status
    status = "ACCEPTED" if not reasons else "REJECTED"

    # Extract meta‑rules (always performed – useful for audit even on acceptance)
    meta_rules = _extract_meta_rules(rule_text)

    return {
        "status": status,
        "reasons": reasons,
        "meta_rules": meta_rules,
    }


# ---------------------------------------------------------------------------
# Simple CLI for manual testing (not used in production)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python rlif_rule_verifier.py <rule_file>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        rule_content = f.read()

    result = verify_rule(rule_content)
    print("Verification result:")
    print(f"  Status : {result['status']}")
    if result["reasons"]:
        print("  Reasons:")
        for r in result["reasons"]:
            print(f"    - {r}")
    if result["meta_rules"]:
        print("  Extracted meta‑rules:")
        for k, v in result["meta_rules"].items():
            print(f"    {k} = {v}")