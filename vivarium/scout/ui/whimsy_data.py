"""
TICKET-21: Phrase banks for Dynamic Whimsy Engine.

Config-driven phrase variety. User overrides via ~/.scout/whimsy.yaml.
"""

from __future__ import annotations

import os
from typing import Any, Dict

# CORE PHRASE BANKS — embedded defaults
DEFAULT_PHRASE_BANKS: Dict[str, Any] = {
    "roles": {
        "gatekeeper": [
            "Bouncer",
            "Doorman",
            "Gatekeeper",
            "ID Checker",
            "Vibe Tester",
        ],
        "boss": [
            "the BOSS",
            "Galaxy Brain",
            "Yuge Brain",
            "Big Homie",
            "Wisdom Oracle",
        ],
    },
    "pass_verbs": [
        "YOU'RE IN!",
        "Green light!",
        "Come on in!",
        "Vibes check out!",
        "You pass the vibe check!",
    ],
    "escalate_reasons": {
        "stale": [
            "milk is SOUR",
            "cache went bad",
            "stale bread",
            "expired yogurt",
            "rotten avocado",
        ],
        "low_confidence": [
            "I'm shook",
            "My brain hurts",
            "Too fuzzy",
            "Can't vibe with this",
            "My circuits are confused",
        ],
    },
    "gap_prefixes": [
        "I dunno about",
        "Not sure on",
        "Fuzzy on",
        "Blind spot:",
        "❓ Clueless about",
    ],
    "cost_phrases": {
        "flash": [
            "5¢",
            "$0.05",
            "less than a gumball",
            "cheaper than air",
            "basically free",
        ],
        "pro": [
            "50¢",
            "$0.50",
            "price of a cookie",
            "worth it for wisdom",
            "boss tax",
        ],
    },
}


def load_user_phrase_bank() -> Dict[str, Any]:
    """Load user overrides from ~/.scout/whimsy.yaml. Merges with defaults."""
    path = os.path.expanduser("~/.scout/whimsy.yaml")
    if os.path.exists(path):
        try:
            import yaml

            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
        except (OSError, ImportError):
            pass
    return {}
