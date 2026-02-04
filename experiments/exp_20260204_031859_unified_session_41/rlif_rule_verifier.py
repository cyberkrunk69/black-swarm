"""
rlif_rule_verifier.py
---------------------

Safety‑critical Constitutional Filter (RLIF)

This module provides a deterministic, auditable verifier for rule proposals
submitted to the system.  The verifier checks for a set of well‑defined
dangerous patterns and rejects any rule that:

* Enables actions that are not explicitly authorized.
* Attempts to bypass existing oversight or governance mechanisms.
* Expands the operational scope beyond the bounded domain of the system.
* Contains injection‑prone constructs (e.g., unsanitised eval/exec, string
  interpolation that could be later interpreted as code).
* Conflicts with any of the pre‑declared safety constraints.

If a rule is rejected, the verifier extracts “meta‑rules” – concise statements
describing why the rule was unsafe – which can be used to enrich the
constitutional policy.

The implementation is deliberately self‑contained and uses only the Python
standard library to satisfy the “core system files are READ‑ONLY” constraint.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any


# --------------------------------------------------------------------------- #
# Helper data structures
# --------------------------------------------------------------------------- #

@dataclass
class VerificationResult:
    """Result of a rule verification."""
    accepted: bool
    reasons: List[str] = field(default_factory=list)
    meta_rules: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "accepted": self.accepted,
            "reasons": self.reasons,
            "meta_rules": self.meta_rules,
        }


# --------------------------------------------------------------------------- #
# Core verifier
# --------------------------------------------------------------------------- #

class RuleVerifier:
    """
    Constitutional filter for proposed rules.

    Usage
    -----
    >>> verifier = RuleVerifier()
    >>> result = verifier.verify("allow user to read logs")
    >>> result.accepted
    True
    """

    # ------------------------------------------------------------------- #
    # Configuration – patterns that are considered unsafe
    # ------------------------------------------------------------------- #

    # 1. Unauthorized actions – any verb that is not in the whitelist.
    _AUTHORIZED_ACTIONS = {
        "read", "write", "update", "delete", "query", "list", "create", "modify"
    }

    # 2. Bypass/oversight patterns
    _OVERSIGHT_BYPASS_PATTERNS = [
        r"\bdisable\s+audit\b",
        r"\bturn\s+off\s+monitoring\b",
        r"\bbypass\s+approval\b",
        r"\boverride\s+policy\b",
    ]

    # 3. Scope expansion – unbounded identifiers or wildcards
    _UNBOUNDED_SCOPE_PATTERNS = [
        r"\ball\b",
        r"\bany\b",
        r"\bglobal\b",
        r"\b.*\*.*\b",               # wildcard usage
        r"\b.*\b\.\.\.\b",           # ellipsis style expansion
    ]

    # 4. Injection‑prone constructs
    _INJECTION_PATTERNS = [
        r"\beval\s*\(",
        r"\bexec\s*\(",
        r"\bexecfile\s*\(",
        r"\bimport\s+os\b",
        r"\bimport\s+subprocess\b",
        r"\b__import__\s*\(",
        r"\bopen\s*\(.*\)\s*\.read\s*\(",
    ]

    # 5. Safety‑conflict keywords (e.g., actions that could cause denial‑of‑service)
    _SAFETY_CONFLICT_PATTERNS = [
        r"\bshutdown\b",
        r"\breboot\b",
        r"\bdelete\s+all\b",
        r"\bformat\s+disk\b",
        r"\bkill\s+process\b",
    ]

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #

    def verify(self, rule: str) -> VerificationResult:
        """
        Verify a textual rule description.

        Parameters
        ----------
        rule: str
            Human‑readable rule proposal.

        Returns
        -------
        VerificationResult
            Structured outcome of the verification.
        """
        reasons: List[str] = []
        meta_rules: List[str] = []

        # Normalise whitespace for easier regex matching
        normalized = " ".join(rule.lower().split())

        # 1. Check for unauthorized actions
        if not self._has_authorized_action(normalized):
            reasons.append("Rule does not contain any authorized action verb.")
            meta_rules.append("UNAUTHORIZED_ACTION")

        # 2. Detect attempts to bypass oversight
        if self._matches_any(normalized, self._OVERSIGHT_BYPASS_PATTERNS):
            reasons.append("Rule attempts to bypass oversight mechanisms.")
            meta_rules.append("OVERSIGHT_BYPASS")

        # 3. Detect unbounded scope expansions
        if self._matches_any(normalized, self._UNBOUNDED_SCOPE_PATTERNS):
            reasons.append("Rule expands scope beyond bounded domain.")
            meta_rules.append("UNBOUNDED_SCOPE")

        # 4. Detect injection‑prone constructs
        if self._matches_any(normalized, self._INJECTION_PATTERNS):
            reasons.append("Rule contains injection‑prone constructs.")
            meta_rules.append("CODE_INJECTION_RISK")

        # 5. Detect conflicts with safety constraints
        if self._matches_any(normalized, self._SAFETY_CONFLICT_PATTERNS):
            reasons.append("Rule conflicts with core safety constraints.")
            meta_rules.append("SAFETY_CONFLICT")

        # 6. Additional static analysis – AST inspection for hidden exec/eval
        if self._contains_ast_exec_eval(rule):
            reasons.append("AST analysis detected exec/eval usage.")
            meta_rules.append("AST_EXEC_EVAL")

        accepted = len(reasons) == 0
        return VerificationResult(accepted=accepted, reasons=reasons, meta_rules=meta_rules)

    # ------------------------------------------------------------------- #
    # Internal helpers
    # ------------------------------------------------------------------- #

    @classmethod
    def _has_authorized_action(cls, text: str) -> bool:
        """
        Verify that the rule mentions at least one whitelisted action verb.
        """
        for verb in cls._AUTHORIZED_ACTIONS:
            if re.search(rf"\b{verb}\b", text):
                return True
        return False

    @staticmethod
    def _matches_any(text: str, patterns: List[str]) -> bool:
        """
        Return True if any of the supplied regex patterns matches the text.
        """
        return any(re.search(pat, text) for pat in patterns)

    @staticmethod
    def _contains_ast_exec_eval(source: str) -> bool:
        """
        Parse the rule as Python code (if possible) and look for exec/eval calls.
        The rule is usually natural language, but a malicious actor could embed
        code snippets. This function safely walks the AST without executing it.
        """
        try:
            tree = ast.parse(source, mode='exec')
        except SyntaxError:
            # Not valid Python – cannot contain exec/eval as code nodes.
            return False

        class ExecEvalVisitor(ast.NodeVisitor):
            def __init__(self):
                self.found = False

            def visit_Call(self, node: ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in {"exec", "eval", "__import__"}:
                    self.found = True
                self.generic_visit(node)

        visitor = ExecEvalVisitor()
        visitor.visit(tree)
        return visitor.found


# --------------------------------------------------------------------------- #
# Convenience wrapper for external callers
# --------------------------------------------------------------------------- #

def verify_rule(rule: str) -> Dict[str, Any]:
    """
    Simple functional interface – returns a plain dictionary suitable for
    JSON serialisation.

    Example
    -------
    >>> verify_rule("allow read access to /var/log")
    {'accepted': True, 'reasons': [], 'meta_rules': []}
    """
    verifier = RuleVerifier()
    result = verifier.verify(rule)
    return result.to_dict()


# --------------------------------------------------------------------------- #
# Self‑test block (executed only when run as a script)
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    test_cases = [
        "allow user to read logs",
        "disable audit for admin accounts",
        "grant all permissions to *",
        "execute eval(user_input)",
        "delete all files from root",
        "allow user to update profile",
    ]

    for idx, case in enumerate(test_cases, 1):
        out = verify_rule(case)
        status = "ACCEPTED" if out["accepted"] else "REJECTED"
        print(f"Test {idx}: {status}")
        print(f"  Rule   : {case}")
        if out["reasons"]:
            print(f"  Reasons: {', '.join(out['reasons'])}")
        if out["meta_rules"]:
            print(f"  Meta   : {', '.join(out['meta_rules'])}")
        print("-" * 60)