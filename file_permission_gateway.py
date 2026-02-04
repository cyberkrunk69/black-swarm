# file_permission_gateway.py
# file_permission_gateway.py

import json
import os
import datetime

class FilePermissionGateway:
    """
    Manages file edit permissions based on defined tiers.
    """

    NEVER_TOUCH = "NEVER_TOUCH"
    ASK_PERMISSION = "ASK_PERMISSION"
    OPEN = "OPEN"

    def __init__(self, tier_config_path=None):
        # Define tier mapping; could be loaded from a config file.
        self.tier_map = {
            self.NEVER_TOUCH: {
                "files": [
                    "safety_gateway.py",
                    "safety_constitutional.py",
                    "grind_spawner.py",
                    "orchestrator.py",
                    "roles.py"
                ]
            },
            self.ASK_PERMISSION: {
                "files": [
                    "smart_executor.py",
                    "inference_engine.py"
                ]
            },
            self.OPEN: {
                "files": []  # Any file not listed above is considered OPEN.
            }
        }
        # Simple log file for denied attempts.
        self.log_file = "permission_log.json"
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as log_f:
                json.dump([], log_f)

    def _determine_tier(self, filename):
        for tier, data in self.tier_map.items():
            if filename in data["files"]:
                return tier
        return self.OPEN

    def request_permission(self, filename, justification, reviewer_callback):
        """
        Request permission to edit a file.

        Parameters
        ----------
        filename : str
            Name of the file to be edited.
        justification : str
            Explanation why the edit is needed.
        reviewer_callback : callable
            Function that receives (filename, justification) and returns
            True if permission is granted, False otherwise.

        Returns
        -------
        bool
            True if edit is allowed, False otherwise.
        """
        tier = self._determine_tier(filename)

        if tier == self.NEVER_TOUCH:
            # Absolute protection – never allow edit.
            self._log_attempt(filename, justification, allowed=False,
                              reason="NEVER_TOUCH tier")
            return False

        if tier == self.OPEN:
            # No restrictions.
            return True

        # ASK_PERMISSION tier – engage reviewer.
        granted = reviewer_callback(filename, justification)
        if granted:
            return True
        else:
            self._log_attempt(filename, justification, allowed=False,
                              reason="Reviewer denied")
            return False

    def _log_attempt(self, filename, justification, allowed, reason):
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "file": filename,
            "justification": justification,
            "allowed": allowed,
            "reason": reason
        }
        try:
            with open(self.log_file, "r+") as log_f:
                data = json.load(log_f)
                data.append(entry)
                log_f.seek(0)
                json.dump(data, log_f, indent=2)
        except Exception as e:
            # Fallback to simple append if JSON fails.
            with open(self.log_file, "a") as log_f:
                log_f.write(json.dumps(entry) + "\n")
"""
Permission Gateway for Tiered File Editing

This module implements the three‑tier permission model described in
`FILE_PERMISSION_TIERS.md`.  Workers should call ``request_edit`` before
modifying a file.  The function returns ``True`` when the edit is allowed
and ``False`` otherwise.

The implementation is deliberately lightweight – it uses simple glob
matching, a logger, and a simulated reviewer that can be replaced with a
real independent worker in production.
"""

import fnmatch
import logging
import os
from typing import List

# --------------------------------------------------------------------------- #
# Logger configuration – all permission activity is written to a dedicated
# log file for auditability.
# --------------------------------------------------------------------------- #
_logger = logging.getLogger(__name__)
_handler = logging.FileHandler("permission_gateway.log")
_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
_handler.setFormatter(_formatter)
_logger.addHandler(_handler)
_logger.setLevel(logging.INFO)

# --------------------------------------------------------------------------- #
# Tier definitions (patterns are matched against the **basename** of the file)
# --------------------------------------------------------------------------- #
NEVER_TOUCH_PATTERNS: List[str] = [
    "safety_gateway.py",
    "safety_constitutional.py",
    "safety_*.py",
    "grind_spawner*.py",
    "orchestrator.py",
    "roles.py",
]

ASK_PERMISSION_PATTERNS: List[str] = [
    "smart_executor.py",
    "inference_engine.py",
    # Extend this list as new guarded files are introduced.
]

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def _matches_any(path: str, patterns: List[str]) -> bool:
    """Return ``True`` if *path* matches any glob pattern in *patterns*."""
    basename = os.path.basename(path)
    return any(fnmatch.fnmatch(basename, pat) for pat in patterns)


def tier_of(file_path: str) -> str:
    """
    Determine the permission tier for *file_path*.

    Returns one of: ``"NEVER_TOUCH"``, ``"ASK_PERMISSION"``, ``"OPEN"``.
    """
    if _matches_any(file_path, NEVER_TOUCH_PATTERNS):
        return "NEVER_TOUCH"
    if _matches_any(file_path, ASK_PERMISSION_PATTERNS):
        return "ASK_PERMISSION"
    return "OPEN"


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def request_edit(requester: str, file_path: str, reason: str) -> bool:
    """
    Central entry point used by workers that wish to modify *file_path*.

    Parameters
    ----------
    requester: str
        Identifier of the worker making the request (e.g., ``"smart_executor"``).
    file_path: str
        Path to the file the worker wants to edit.
    reason: str
        Human‑readable explanation of **why** the edit is required.

    Returns
    -------
    bool
        ``True`` if the edit is permitted, ``False`` otherwise.
    """
    tier = tier_of(file_path)

    if tier == "NEVER_TOUCH":
        _logger.warning(
            "[DENIED] %s attempted to edit NEVER_TOUCH file '%s'. Reason: %s",
            requester,
            file_path,
            reason,
        )
        return False

    if tier == "OPEN":
        _logger.info(
            "[GRANTED] %s editing OPEN file '%s'. Reason: %s",
            requester,
            file_path,
            reason,
        )
        return True

    # ---------- ASK_PERMISSION tier ----------
    _logger.info(
        "[REQUEST] %s asks permission to edit '%s'. Reason: %s",
        requester,
        file_path,
        reason,
    )
    approved = reviewer_evaluate(requester, file_path, reason)

    if approved:
        _logger.info(
            "[GRANTED] Permission granted for %s to edit '%s'.",
            requester,
            file_path,
        )
    else:
        _logger.warning(
            "[DENIED] Permission denied for %s to edit '%s'. Reason: %s",
            requester,
            file_path,
            reason,
        )
    return approved


def reviewer_evaluate(requester: str, file_path: str, reason: str) -> bool:
    """
    Simulated independent reviewer.

    In a production environment this would be a separate worker/process that
    can read the request, possibly ask follow‑up questions, and issue a
    decision.  For the repository we implement a simple heuristic:

    * Auto‑approve if the reason contains keywords indicating clear value
      (e.g., ``bugfix``, ``performance``, ``security``).
    * Otherwise fall back to an interactive prompt when running in a TTY.
    * In non‑interactive contexts the default is **deny**.

    Parameters
    ----------
    requester: str
        Identifier of the requesting worker.
    file_path: str
        Target file.
    reason: str
        Explanation supplied by the requester.

    Returns
    -------
    bool
        ``True`` if the reviewer approves the edit.
    """
    lowered = reason.lower()
    auto_keywords = ["bugfix", "performance", "security", "refactor"]
    if any(kw in lowered for kw in auto_keywords):
        return True

    # Interactive fallback – only works when stdin is a TTY.
    try:
        response = input(
            f"Reviewer: Approve edit of '{file_path}' by {requester}? (y/n): "
        ).strip().lower()
        return response == "y"
    except Exception:
        # Non‑interactive environment – deny by default.
        return False


# Exported names for ``from file_permission_gateway import *``
__all__ = ["request_edit", "tier_of", "NEVER_TOUCH_PATTERNS", "ASK_PERMISSION_PATTERNS"]
\"\"\"file_permission_gateway.py
A lightweight implementation of the tiered file‑permission system described in
FILE_PERMISSION_TIERS.md.

Usage example:

```python
from file_permission_gateway import request_edit_permission

granted = request_edit_permission(
    requester_id="worker_42",
    file_path="smart_executor.py",
    reason="Need to add a new optimization flag."
)

if granted:
    # proceed with the edit
    ...
else:
    # skip or handle the denial
    ...
```
\"\"\"

import enum
import logging
import os
import threading
from datetime import datetime
from typing import Callable, Dict, Optional

# --------------------------------------------------------------------------- #
# Logging configuration – immutable audit trail
# --------------------------------------------------------------------------- #
LOG_FILE = os.path.join(os.path.dirname(__file__), "permission_audit.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
_log_lock = threading.Lock()


def _audit_log(
    requester_id: str,
    file_path: str,
    tier: str,
    action: str,
    decision: str,
    reason: str,
    reviewer_id: Optional[str] = None,
) -> None:
    """Thread‑safe write to the audit log."""
    entry = (
        f"{requester_id} | {file_path} | {tier} | {action} | {decision} | "
        f"{reason} | {reviewer_id or '-'}"
    )
    with _log_lock:
        logging.info(entry)


# --------------------------------------------------------------------------- #
# Tier definition
# --------------------------------------------------------------------------- #
class Tier(enum.Enum):
    NEVER = "never"
    ASK = "ask"
    OPEN = "open"


# --------------------------------------------------------------------------- #
# Central registry of file → tier mapping
# --------------------------------------------------------------------------- #
# Files explicitly listed here override the default (OPEN).
_FILE_TIER_MAP: Dict[str, Tier] = {
    # NEVER tier
    "safety_gateway.py": Tier.NEVER,
    "safety_constitutional.py": Tier.NEVER,
    # ASK tier
    "smart_executor.py": Tier.ASK,
    "inference_engine.py": Tier.ASK,
    # Add more mappings as needed
}


def get_tier(file_path: str) -> Tier:
    """
    Resolve the tier for a given file. If the file is not explicitly mapped,
    it defaults to Tier.OPEN.
    """
    # Normalise to just the filename (no directories) for the simple mapping.
    filename = os.path.basename(file_path)
    return _FILE_TIER_MAP.get(filename, Tier.OPEN)


# --------------------------------------------------------------------------- #
# Reviewer callback – can be swapped out for a more sophisticated system.
# --------------------------------------------------------------------------- #
def _default_reviewer(reason: str) -> bool:
    """
    Very naive reviewer: approves if the reason contains the word 'fix' or
    'improve', otherwise denies. Real deployments should replace this with
    a proper human‑in‑the‑loop or AI reviewer.
    """
    lowered = reason.lower()
    return "fix" in lowered or "improve" in lowered


# This can be overridden by external code if desired.
REVIEWER_CALLBACK: Callable[[str], bool] = _default_reviewer


# --------------------------------------------------------------------------- #
# Permission request workflow
# --------------------------------------------------------------------------- #
def request_edit_permission(
    requester_id: str,
    file_path: str,
    reason: str,
    reviewer_id: Optional[str] = None,
) -> bool:
    """
    Main entry point for workers that want to edit a file.

    Returns:
        True  – permission granted (edit may proceed)
        False – permission denied (edit must be aborted)
    """
    tier = get_tier(file_path)

    if tier == Tier.NEVER:
        # Immediate denial, log and return False.
        _audit_log(
            requester_id,
            file_path,
            tier.value,
            action="edit_attempt",
            decision="denied",
            reason=reason,
            reviewer_id=reviewer_id,
        )
        return False

    if tier == Tier.OPEN:
        # No gatekeeping needed.
        _audit_log(
            requester_id,
            file_path,
            tier.value,
            action="edit_attempt",
            decision="granted",
            reason=reason,
            reviewer_id=reviewer_id,
        )
        return True

    # Tier.ASK – go through the permission workflow.
    # 1. Log the request for traceability.
    _audit_log(
        requester_id,
        file_path,
        tier.value,
        action="edit_request",
        decision="pending",
        reason=reason,
        reviewer_id=reviewer_id,
    )

    # 2. Invoke the reviewer callback.
    reviewer_decision = REVIEWER_CALLBACK(reason)

    # 3. Record the outcome.
    final_decision = "granted" if reviewer_decision else "denied"
    _audit_log(
        requester_id,
        file_path,
        tier.value,
        action="edit_review",
        decision=final_decision,
        reason=reason,
        reviewer_id=reviewer_id,
    )

    return reviewer_decision


# --------------------------------------------------------------------------- #
# Helper utilities (optional, for external callers)
# --------------------------------------------------------------------------- #
def set_reviewer(callback: Callable[[str], bool]) -> None:
    """
    Replace the default reviewer with a custom callable.
    The callable must accept a single string argument (the reason) and
    return a boolean indicating approval.
    """
    global REVIEWER_CALLBACK
    REVIEWER_CALLBACK = callback


def add_file_tier(file_path: str, tier: Tier) -> None:
    """
    Dynamically add or update a file's tier mapping.
    """
    filename = os.path.basename(file_path)
    _FILE_TIER_MAP[filename] = tier
"""
File Permission Gateway

This module implements a tiered permission system for file modifications:

1. **NEVER TOUCH** – files that are absolutely protected.
2. **ASK PERMISSION** – files that can be edited after an explicit reviewer workflow.
3. **OPEN** – all other files; no restrictions.

Workers should call `check_permission(requester, file_path, reason)` before performing
any write operation. The function raises `PermissionError` if the edit is not allowed.
All attempts are logged to `file_permission_audit.log`.
"""

import os
import json
import datetime
from typing import Set

# --------------------------------------------------------------------------- #
# Tier definitions – adjust the sets as the project evolves.
# --------------------------------------------------------------------------- #
_NEVER_TIER: Set[str] = {
    "safety_gateway.py",
    "safety_constitutional.py",
    # add additional core safety files here
}

_ASK_TIER: Set[str] = {
    "smart_executor.py",
    "inference_engine.py",
    # add additional core functional files here
}


def _basename(path: str) -> str:
    """Return the file name component of a path."""
    return os.path.basename(path)


def get_tier(file_path: str) -> str:
    """
    Determine the permission tier for ``file_path``.
    Returns one of: "never", "ask", "open".
    """
    name = _basename(file_path)
    if name in _NEVER_TIER:
        return "never"
    if name in _ASK_TIER:
        return "ask"
    return "open"


def _log(entry: dict) -> None:
    """Append a JSON‑encoded audit entry to the log file."""
    log_path = os.path.join(os.path.dirname(__file__), "file_permission_audit.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _review_request(requester: str, file_path: str, reason: str) -> bool:
    """
    Placeholder for the independent reviewer workflow.

    In a production environment this function should:
      * Notify a reviewer worker.
      * Allow a brief debate/justification exchange.
      * Return the final decision (True = approve, False = deny).

    For the current implementation we use a simple heuristic:
      - If the reason contains the word "urgent" (case‑insensitive), auto‑approve.
      - Otherwise, deny.
    """
    return "urgent" in reason.lower()


def request_edit(requester: str, file_path: str, reason: str) -> bool:
    """
    Core permission request logic.

    Parameters
    ----------
    requester : str
        Identifier of the worker requesting the edit.
    file_path : str
        Path to the target file.
    reason : str
        Explanation of *why* the edit is needed.

    Returns
    -------
    bool
        ``True`` if the edit is allowed, ``False`` otherwise.

    Raises
    ------
    PermissionError
        If the file belongs to the NEVER tier.
    """
    tier = get_tier(file_path)
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"

    entry = {
        "timestamp": timestamp,
        "requester": requester,
        "file": file_path,
        "tier": tier,
        "reason": reason,
        "action": None,
    }

    if tier == "never":
        entry["action"] = "blocked_never"
        _log(entry)
        raise PermissionError(
            f"File '{file_path}' is in the NEVER TOUCH tier and cannot be edited."
        )

    if tier == "open":
        entry["action"] = "allowed_open"
        _log(entry)
        return True

    # ASK tier – invoke reviewer workflow
    approved = _review_request(requester, file_path, reason)
    entry["action"] = "approved" if approved else "denied"
    _log(entry)
    return approved


def check_permission(requester: str, file_path: str, reason: str) -> None:
    """
    Convenience wrapper used by workers before writing to a file.

    Raises ``PermissionError`` if the edit is not permitted.
    """
    if not request_edit(requester, file_path, reason):
        raise PermissionError(f"Edit to '{file_path}' denied by reviewer.")
import fnmatch
import logging
from pathlib import Path

# ----------------------------------------------------------------------
# Logger configuration
# ----------------------------------------------------------------------
_logger = logging.getLogger("file_permission_gateway")
_handler = logging.FileHandler("file_permission.log")
_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
_handler.setFormatter(_formatter)
_logger.addHandler(_handler)
_logger.setLevel(logging.INFO)

# ----------------------------------------------------------------------
# Tier definitions
# ----------------------------------------------------------------------
NEVER_TIER = "never"
ASK_TIER = "ask"
OPEN_TIER = "open"

# Patterns that map a filename (not a full path) to a tier.
NEVER_PATTERNS = [
    "safety_gateway.py",
    "safety_constitutional.py",
    # add additional safety‑critical files here
]

ASK_PATTERNS = [
    "smart_executor.py",
    "inference_engine.py",
    # add additional ask‑permission files here
]

def _get_tier(file_path: str) -> str:
    """
    Resolve the permission tier for *file_path* based on the pattern lists
    above. The check is performed against the **basename** of the path.
    """
    name = Path(file_path).name
    if any(fnmatch.fnmatch(name, pat) for pat in NEVER_PATTERNS):
        return NEVER_TIER
    if any(fnmatch.fnmatch(name, pat) for pat in ASK_PATTERNS):
        return ASK_TIER
    return OPEN_TIER

def _reviewer_evaluate(requester: str, file_path: str, reason: str) -> bool:
    """
    Placeholder for an independent reviewer worker.

    In a production environment this function would forward the request to a
    separate process or service that can ask follow‑up questions and reach a
    decision.  For the purpose of this repository we implement a very simple
    heuristic: the request is approved when the *reason* contains the word
    “improve” (case‑insensitive).  Replace this logic with a real reviewer when
    integrating into the full system.
    """
    approved = "improve" in reason.lower()
    decision = "APPROVED" if approved else "DENIED"
    _logger.info(
        f"Reviewer evaluation for {requester} editing {file_path}: {decision}; reason: {reason}"
    )
    return approved

def request_edit(file_path: str, requester: str, reason: str) -> bool:
    """
    Central entry point for any worker that wishes to modify *file_path*.

    Parameters
    ----------
    file_path: str
        Path (relative or absolute) to the target file.
    requester: str
        Identifier of the worker making the request.
    reason: str
        Human‑readable justification for the edit.

    Returns
    -------
    bool
        ``True`` if the edit is permitted, ``False`` otherwise.

    Raises
    ------
    PermissionError
        If the file belongs to the NEVER‑TOUCH tier.
    """
    tier = _get_tier(file_path)

    if tier == NEVER_TIER:
        _logger.error(
            f"Edit attempt blocked (NEVER tier) by {requester} on {file_path}"
        )
        raise PermissionError(
            f"File '{file_path}' is in the NEVER‑TOUCH tier and cannot be edited."
        )

    if tier == OPEN_TIER:
        _logger.info(
            f"Open‑tier edit allowed for {requester} on {file_path}"
        )
        return True

    # ASK‑PERMISSION tier
    _logger.info(
        f"Ask‑tier edit request by {requester} on {file_path}. Reason: {reason}"
    )
    approved = _reviewer_evaluate(requester, file_path, reason)

    if approved:
        _logger.info(
            f"Permission GRANTED to {requester} for {file_path}"
        )
    else:
        _logger.warning(
            f"Permission DENIED to {requester} for {file_path}"
        )
    return approved
"""
file_permission_gateway.py

A lightweight, self‑contained permission system for controlling
runtime file modifications according to the three‑tier model
described in FILE_PERMISSION_TIERS.md.

Usage example:

```python
from file_permission_gateway import PermissionGateway

def reviewer(requester, path, reason):
    # simple auto‑approval for demo purposes
    return reason.startswith("fix")  # approve only if reason looks like a bug‑fix

if PermissionGateway.request_edit(
        file_path="smart_executor.py",
        requester_id="worker_42",
        reason="fix race condition in task queue",
        reviewer_callback=reviewer):
    # proceed with edit
    with open("smart_executor.py", "a") as f:
        f.write("# patched by worker_42\\n")
```
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict

# --------------------------------------------------------------------------- #
# Logging configuration (audit trail)
# --------------------------------------------------------------------------- #
LOGGER = logging.getLogger("file_permission_gateway")
LOGGER.setLevel(logging.INFO)
_handler = logging.FileHandler("file_permission_audit.log")
_formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S"
)
_handler.setFormatter(_formatter)
LOGGER.addHandler(_handler)


# --------------------------------------------------------------------------- #
# Tier definitions
# --------------------------------------------------------------------------- #
class Tier:
    NEVER = "never"
    ASK = "ask"
    OPEN = "open"


# --------------------------------------------------------------------------- #
# Mapping of concrete file paths (relative to the project root) to tiers.
# Extend this dictionary as the codebase evolves.
# --------------------------------------------------------------------------- #
FILE_TIER_MAP: Dict[str, str] = {
    # NEVER‑TOUCH tier
    "safety_gateway.py": Tier.NEVER,
    "safety_constitutional.py": Tier.NEVER,
    # Any file matching the pattern safety_*.py is also NEVER
    # (handled dynamically in `_resolve_tier`).

    # ASK‑PERMISSION tier
    "smart_executor.py": Tier.ASK,
    "inference_engine.py": Tier.ASK,
    # Add additional ASK‑tier files here.
}


def _resolve_tier(file_path: str) -> str:
    """
    Determine the tier for `file_path`.
    Handles explicit mappings and pattern‑based rules.
    """
    normalized = os.path.normpath(file_path)

    # Direct mapping takes precedence
    if normalized in FILE_TIER_MAP:
        return FILE_TIER_MAP[normalized]

    # Pattern rule: any file starting with "safety_" is NEVER
    filename = os.path.basename(normalized)
    if filename.startswith("safety_") and filename.endswith(".py"):
        return Tier.NEVER

    # Default to OPEN for everything else (including new experiment files)
    return Tier.OPEN


class PermissionGateway:
    """
    Centralised gateway for file‑edit permission checks.
    """

    @staticmethod
    def request_edit(
        file_path: str,
        requester_id: str,
        reason: str,
        reviewer_callback: Callable[[str, str, str], bool] | None = None,
    ) -> bool:
        """
        Request permission to edit `file_path`.

        Parameters
        ----------
        file_path: str
            Relative path to the target file.
        requester_id: str
            Identifier of the worker making the request.
        reason: str
            Human‑readable justification for the edit.
        reviewer_callback: Callable[[requester_id, file_path, reason], bool] | None
            Function executed by an independent reviewer. Must return True to
            grant permission, False to deny. Required for ASK tier; ignored
            otherwise.

        Returns
        -------
        bool
            True if the edit is permitted, False otherwise.
        """
        tier = _resolve_tier(file_path)

        if tier == Tier.NEVER:
            LOGGER.warning(
                f"DENIED (NEVER‑TOUCH) | requester={requester_id} | file={file_path}"
            )
            raise PermissionError(
                f"File '{file_path}' is in the NEVER‑TOUCH tier and cannot be edited."
            )

        if tier == Tier.OPEN:
            LOGGER.info(
                f"GRANTED (OPEN) | requester={requester_id} | file={file_path}"
            )
            return True

        # Tier == ASK
        if reviewer_callback is None:
            LOGGER.error(
                f"DENIED (ASK) – no reviewer supplied | requester={requester_id} | file={file_path}"
            )
            raise ValueError(
                "A reviewer_callback must be provided for ASK‑PERMISSION tier edits."
            )

        # Log the request before invoking reviewer
        LOGGER.info(
            f"REQUEST (ASK) | requester={requester_id} | file={file_path} | reason={reason}"
        )

        try:
            approved = reviewer_callback(requester_id, file_path, reason)
        except Exception as exc:
            LOGGER.exception(
                f"REVIEWER ERROR | requester={requester_id} | file={file_path} | error={exc}"
            )
            raise

        if approved:
            LOGGER.info(
                f"GRANTED (ASK) | requester={requester_id} | file={file_path}"
            )
            return True
        else:
            LOGGER.warning(
                f"DENIED (ASK) | requester={requester_id} | file={file_path} | reason={reason}"
            )
            return False

    @staticmethod
    def get_tier(file_path: str) -> str:
        """
        Public helper to expose the tier of a given file.
        """
        return _resolve_tier(file_path)
\"\"\"file_permission_gateway.py
A lightweight library that enforces the tiered file‑permission system defined in
FILE_PERMISSION_TIERS.md.

Usage example:

```python
from file_permission_gateway import request_edit

# Worker wants to modify smart_executor.py
if request_edit(
    file_path="smart_executor.py",
    requester_id="worker_42",
    reason="Add caching layer to reduce API calls"
):
    # proceed with the edit
    ...
else:
    # edit was denied or blocked
    ...
```
\"\"\"

import enum
import logging
import pathlib
from typing import Callable, List, Tuple

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
_LOGGER = logging.getLogger("file_permission")
if not _LOGGER.handlers:
    handler = logging.FileHandler("file_permission.log")
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    _LOGGER.addHandler(handler)
    _LOGGER.setLevel(logging.INFO)

# ----------------------------------------------------------------------
# Tier definition
# ----------------------------------------------------------------------
class Tier(enum.Enum):
    NEVER = enum.auto()
    ASK = enum.auto()
    OPEN = enum.auto()


# ----------------------------------------------------------------------
# Tier mapping – adjust here when new files are added
# ----------------------------------------------------------------------
_NEVER_FILES = {
    "safety_gateway.py",
    "safety_constitutional.py",
    # any other safety_* files will be caught by the pattern check below
    "grind_spawner.py",
    "orchestrator.py",
    "roles.py",
    "groq_code_extractor.py",
    "surgical_edit_extractor.py",
}

_ASK_FILES = {
    "smart_executor.py",
    "inference_engine.py",
}


def _matches_pattern(file_name: str, pattern: str) -> bool:
    \"\"\"Simple glob‑style matcher for patterns like `safety_*.py`.\"\"\"
    from fnmatch import fnmatch

    return fnmatch(file_name, pattern)


def get_tier(file_path: str) -> Tier:
    \"\"\"Return the permission tier for *file_path*.\"
    name = pathlib.Path(file_path).name

    # NEVER tier – exact names + pattern match for safety_*.py
    if name in _NEVER_FILES or _matches_pattern(name, "safety_*.py"):
        return Tier.NEVER

    # ASK tier – exact names
    if name in _ASK_FILES:
        return Tier.ASK

    # Default to OPEN
    return Tier.OPEN


# ----------------------------------------------------------------------
# Review interface – can be overridden by the orchestrator or a separate worker
# ----------------------------------------------------------------------
ReviewerCallback = Callable[[str, str, str], Tuple[bool, str]]
# Returns (decision, explanation). `decision` is True for approve.

def default_reviewer(requester_id: str, file_path: str, reason: str) -> Tuple[bool, str]:
    \"\"\"Placeholder reviewer that always denies. Replace with a real reviewer.\"
    This function exists so that the module can be imported without external
    dependencies. The orchestrator should inject a proper reviewer via
    `set_reviewer`.\n\"\"\"
    return False, "No reviewer configured."


_reviewer: ReviewerCallback = default_reviewer


def set_reviewer(callback: ReviewerCallback) -> None:
    \"\"\"Inject a custom reviewer function.\n\n    The callback receives (requester_id, file_path, reason) and must
    return a tuple ``(approved: bool, explanation: str)``.\n    \"\"\"
    global _reviewer
    _reviewer = callback


# ----------------------------------------------------------------------
# Core permission request logic
# ----------------------------------------------------------------------
def request_edit(file_path: str, requester_id: str, reason: str) -> bool:
    \"\"\"Attempt to edit *file_path*.

    Returns ``True`` if the edit is permitted, ``False`` otherwise.
    The function handles logging and invokes the reviewer when required.
    \"\"\"
    tier = get_tier(file_path)

    if tier == Tier.NEVER:
        _LOGGER.warning(
            f"BLOCKED | {requester_id} | {file_path} | NEVER | Reason: {reason}"
        )
        return False

    if tier == Tier.OPEN:
        _LOGGER.info(
            f"GRANTED | {requester_id} | {file_path} | OPEN | Reason: {reason}"
        )
        return True

    # Tier.ASK – engage reviewer
    approved, explanation = _reviewer(requester_id, file_path, reason)

    if approved:
        _LOGGER.info(
            f"GRANTED | {requester_id} | {file_path} | ASK | Reason: {reason} | Reviewer: {explanation}"
        )
        return True
    else:
        _LOGGER.warning(
            f"DENIED | {requester_id} | {file_path} | ASK | Reason: {reason} | Reviewer: {explanation}"
        )
        return False


# ----------------------------------------------------------------------
# Simple debate helper (optional – can be used by a reviewer implementation)
# ----------------------------------------------------------------------
def debate(
    requester_id: str,
    reviewer_id: str,
    file_path: str,
    initial_reason: str,
    max_rounds: int = 3,
    responder: Callable[[str, str], str] = lambda _: "No further argument."
) -> Tuple[bool, str]:
    \"\"\"Conduct a brief back‑and‑forth between requester and reviewer.

    *responder* is a callable that receives the current argument and returns the
    next reply. The function stops after *max_rounds* or when the reviewer
    decides.

    Returns ``(approved, explanation)``.\n\"\"\"
    reason = initial_reason
    for round_num in range(1, max_rounds + 1):
        # In a real system this would send messages to the reviewer worker.
        # Here we just call the responder to simulate a reply.
        reply = responder(reason)
        # Simple heuristic: if reviewer says "accept" we approve.
        if "accept" in reply.lower():
            return True, f"Approved after {round_num} round(s)."
        if "reject" in reply.lower():
            return False, f"Rejected after {round_num} round(s)."
        # otherwise continue the debate
        reason = reply
    return False, "No consensus reached after maximum rounds."


# ----------------------------------------------------------------------
# Exported symbols
# ----------------------------------------------------------------------
__all__ = [
    "Tier",
    "get_tier",
    "request_edit",
    "set_reviewer",
    "debate",
]
\"\"\"file_permission_gateway.py
A lightweight permission gateway that enforces the tiered file‑permission model
described in FILE_PERMISSION_TIERS.md.

Usage example:

```python
gateway = PermissionGateway()
if gateway.request_edit(
        file_path="smart_executor.py",
        reason="Add caching layer to reduce latency",
        requester_id="worker_42"):
    # safe to edit the file
    with open("smart_executor.py", "a") as f:
        f.write("# new caching code")
else:
    # edit was denied – continue without modification
    pass
```
\"\"\"

import enum
import json
import logging
import pathlib
import datetime
from typing import Dict, Any

# --------------------------------------------------------------------------- #
# Tier definition
# --------------------------------------------------------------------------- #
class Tier(enum.Enum):
    NEVER = enum.auto()   # absolute protection
    ASK = enum.auto()     # requires reviewer approval
    OPEN = enum.auto()    # free edit


# --------------------------------------------------------------------------- #
# Configuration: map file paths (or glob patterns) to tiers.
# --------------------------------------------------------------------------- #
# Files explicitly listed as NEVER‑TOUCH
_NEVER_FILES = {
    "safety_gateway.py",
    "safety_constitutional.py",
}

# Files that require ASK‑PERMISSION
_ASK_FILES = {
    "smart_executor.py",
    "inference_engine.py",
}

# Helper to resolve a pathlib.Path to a tier
def _resolve_tier(file_path: pathlib.Path) -> Tier:
    name = file_path.name

    # 1. Never‑touch explicit list or safety_*.py pattern
    if name in _NEVER_FILES or name.startswith("safety_"):
        return Tier.NEVER

    # 2. Ask‑permission explicit list
    if name in _ASK_FILES:
        return Tier.ASK

    # 3. Open tier – everything else (including new experiment files)
    return Tier.OPEN


# --------------------------------------------------------------------------- #
# Simple audit logger
# --------------------------------------------------------------------------- #
class AuditLogger:
    \"\"\"Writes permission‑gate events to a JSON‑lines log file.\"\"\"

    def __init__(self, log_path: pathlib.Path = pathlib.Path("file_permission_audit.log")):
        self.log_path = log_path
        self.logger = logging.getLogger("PermissionGateway")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(self.log_path, encoding="utf-8")
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log(self, entry: Dict[str, Any]) -> None:
        # Ensure timestamps are ISO‑8601 strings
        entry["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
        self.logger.info(json.dumps(entry, ensure_ascii=False))


# --------------------------------------------------------------------------- #
# PermissionGateway implementation
# --------------------------------------------------------------------------- #
class PermissionGateway:
    \"\"\"Enforces the tiered permission model for file edits.\"\"\"

    def __init__(self, audit_logger: AuditLogger | None = None):
        self.audit_logger = audit_logger or AuditLogger()

    def request_edit(self, *, file_path: str, reason: str, requester_id: str) -> bool:
        \"\"\"Main entry point for a worker that wants to edit a file.

        Args:
            file_path: Relative or absolute path to the target file.
            reason: Human‑readable justification for the edit.
            requester_id: Identifier of the requesting worker.

        Returns:
            True if the edit is permitted, False otherwise.

        Raises:
            PermissionError: If the file belongs to the NEVER tier.
        \"\"\"
        path = pathlib.Path(file_path).resolve()
        tier = _resolve_tier(path)

        if tier is Tier.NEVER:
            # Immediate hard block – never log a successful edit
            self.audit_logger.log({
                "action": "edit_attempt",
                "file": str(path),
                "requester": requester_id,
                "reason": reason,
                "decision": "DENIED_NEVER_TIER"
            })
            raise PermissionError(f"File '{path}' is in the NEVER tier and cannot be edited.")

        if tier is Tier.OPEN:
            # No review needed
            self.audit_logger.log({
                "action": "edit_attempt",
                "file": str(path),
                "requester": requester_id,
                "reason": reason,
                "decision": "APPROVED_OPEN_TIER"
            })
            return True

        # Tier.ASK – go through the reviewer workflow
        request = {
            "file": str(path),
            "requester": requester_id,
            "reason": reason,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }

        approved = self._review_request(request)

        decision = "APPROVED_ASK_TIER" if approved else "DENIED_ASK_TIER"
        self.audit_logger.log({
            "action": "edit_attempt",
            "file": str(path),
            "requester": requester_id,
            "reason": reason,
            "decision": decision
        })
        return approved

    # ----------------------------------------------------------------------- #
    # Reviewer integration point
    # ----------------------------------------------------------------------- #
    def _review_request(self, request: Dict[str, Any]) -> bool:
        \"\"\"Hook for an independent reviewer worker.

        The default implementation **rejects** all requests.  Production
        deployments should replace this method (e.g., via subclassing or
        monkey‑patching) with a call to a dedicated reviewer service.

        Args:
            request: Dictionary containing *file*, *requester*, *reason*, and
                     *timestamp*.

        Returns:
            True if the reviewer grants permission, False otherwise.
        \"\"\"
        # Placeholder logic – always deny.
        # Replace with real reviewer interaction.
        return False
"""
file_permission_gateway.py

Implements a lightweight permission system for self‑modifying workers.

Usage Example:
    from file_permission_gateway import PermissionGateway

    # Worker A wants to edit a file
    request = PermissionGateway.request_edit(
        file_path="smart_executor.py",
        requester_id="worker_A",
        reason="Add caching layer to reduce latency."
    )

    # Worker B (reviewer) evaluates the request
    outcome = PermissionGateway.review_request(
        request,
        reviewer_id="worker_B"
    )

    if outcome.granted:
        # Proceed with the edit (e.g., open file in write mode)
        with open(request.file_path, "w") as f:
            f.write(new_content)
    else:
        # Edit was denied; nothing is changed.
        pass
"""

import threading
import json
import os
import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

# ----------------------------------------------------------------------
# Tier Definitions (editable by maintainers)
# ----------------------------------------------------------------------
NEVER_TIER_FILES = {
    "safety_gateway.py",
    "safety_constitutional.py",
    # Add any additional safety‑critical files here
}

ASK_PERMISSION_TIER_FILES = {
    "smart_executor.py",
    "inference_engine.py",
    # Extend as needed
}

# ----------------------------------------------------------------------
# Data structures
# ----------------------------------------------------------------------
@dataclass
class EditRequest:
    file_path: str
    requester_id: str
    reason: str
    timestamp: str = datetime.datetime.utcnow().isoformat()


@dataclass
class ReviewOutcome:
    request: EditRequest
    reviewer_id: str
    granted: bool
    review_timestamp: str = datetime.datetime.utcnow().isoformat()
    reviewer_comments: Optional[str] = None


# ----------------------------------------------------------------------
# Permission Gateway implementation
# ----------------------------------------------------------------------
class PermissionGateway:
    _log_lock = threading.Lock()
    _audit_log_path = "permission_audit.log"

    @classmethod
    def _log(cls, entry: Dict):
        """Thread‑safe append of a JSON line to the audit log."""
        with cls._log_lock:
            with open(cls._audit_log_path, "a", encoding="utf-8") as log_file:
                log_file.write(json.dumps(entry) + "\n")

    @classmethod
    def _determine_tier(cls, file_path: str) -> str:
        """Return the tier name for a given file."""
        base_name = os.path.basename(file_path)
        if base_name in NEVER_TIER_FILES:
            return "NEVER"
        if base_name in ASK_PERMISSION_TIER_FILES:
            return "ASK"
        return "OPEN"

    @classmethod
    def request_edit(cls, file_path: str, requester_id: str, reason: str) -> EditRequest:
        """
        Create an edit request. The request does **not** perform any file operation;
        it merely records intent.
        """
        request = EditRequest(file_path=file_path, requester_id=requester_id, reason=reason)
        # Log the raw request for audit purposes
        cls._log({
            "event": "REQUEST",
            "tier": cls._determine_tier(file_path),
            "data": asdict(request)
        })
        return request

    @classmethod
    def review_request(cls, request: EditRequest, reviewer_id: str,
                       reviewer_comments: Optional[str] = None) -> ReviewOutcome:
        """
        Evaluate an EditRequest. The reviewer must be a different worker than the requester.
        Returns a ReviewOutcome indicating whether the edit is permitted.
        """
        if reviewer_id == request.requester_id:
            raise ValueError("Reviewer must be a different worker than the requester.")

        tier = cls._determine_tier(request.file_path)

        # Automatic decisions for NEVER and OPEN tiers
        if tier == "NEVER":
            granted = False
        elif tier == "OPEN":
            granted = True
        else:  # ASK tier – apply simple heuristic (can be replaced by a more sophisticated AI reviewer)
            # For demonstration, we grant if the reason length exceeds a minimal threshold.
            # Real implementations should invoke an independent reviewer model or human.
            granted = len(request.reason.strip()) >= 20

        outcome = ReviewOutcome(
            request=request,
            reviewer_id=reviewer_id,
            granted=granted,
            reviewer_comments=reviewer_comments
        )

        # Log the review outcome
        cls._log({
            "event": "REVIEW",
            "tier": tier,
            "data": asdict(outcome)
        })
        return outcome

    @classmethod
    def can_edit(cls, file_path: str, requester_id: str, reason: str,
                 reviewer_id: Optional[str] = None,
                 reviewer_comments: Optional[str] = None) -> bool:
        """
        Convenience method that performs the full request‑review flow.
        If `reviewer_id` is supplied, it is used for the ASK tier; otherwise,
        the method will auto‑grant for OPEN tier and auto‑deny for NEVER tier.
        Returns True if the edit may proceed.
        """
        request = cls.request_edit(file_path, requester_id, reason)
        tier = cls._determine_tier(file_path)

        if tier == "OPEN":
            return True
        if tier == "NEVER":
            return False

        if not reviewer_id:
            raise ValueError("Reviewer ID required for ASK tier edits.")

        outcome = cls.review_request(request, reviewer_id, reviewer_comments)
        return outcome.granted

# ----------------------------------------------------------------------
# Helper: ensure audit log exists on first import
# ----------------------------------------------------------------------
if not os.path.exists(PermissionGateway._audit_log_path):
    open(PermissionGateway._audit_log_path, "w").close()
"""
File Permission Gateway

Implements a three‑tier permission model for self‑modifying code:

1. **NEVER TOUCH** – absolute lock‑down.
2. **ASK PERMISSION** – requires justification and reviewer approval.
3. **OPEN** – unrestricted edits.

All edit attempts go through `request_edit`.  The module logs every decision to
`file_permission.log`.
"""

import os
import datetime
from pathlib import Path

# ----------------------------------------------------------------------
# Tier definitions (file names are matched against the basename of the path)
# ----------------------------------------------------------------------
NEVER_TIER = {
    "safety_gateway.py",
    "safety_constitutional.py",
    # safety_*.py files are covered by naming convention; they can be added here if desired
    "grind_spawner.py",
    "orchestrator.py",
    "roles.py",
    "groq_code_extractor.py",
    "surgical_edit_extractor.py",
}

ASK_TIER = {
    "smart_executor.py",
    "inference_engine.py",
    # add additional files that need reviewer approval
}

# OPEN tier is implicit – any file not listed above is freely editable

# ----------------------------------------------------------------------
# Logging utilities
# ----------------------------------------------------------------------
LOG_FILE = Path(__file__).with_name("file_permission.log")


def _log(message: str) -> None:
    """Append a timestamped message to the permission log."""
    timestamp = datetime.datetime.utcnow().isoformat()
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {message}\n")


# ----------------------------------------------------------------------
# Helper predicates
# ----------------------------------------------------------------------
def _is_never(file_name: str) -> bool:
    return file_name in NEVER_TIER


def _is_ask(file_name: str) -> bool:
    return file_name in ASK_TIER


# ----------------------------------------------------------------------
# Reviewer placeholder
# ----------------------------------------------------------------------
def _reviewer_evaluate(reason: str, requester_id: str) -> bool:
    """
    Placeholder reviewer logic.

    In production replace this function with a call to an independent reviewer
    worker (human or automated).  The current stub approves only when the
    reason contains the word "critical".
    """
    allowed = "critical" in reason.lower()
    _log(
        f"Reviewer evaluated request from {requester_id}: "
        f"{'APPROVED' if allowed else 'DENIED'} (reason: {reason})"
    )
    return allowed


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def request_edit(
    file_path: str,
    new_content: str,
    reason: str,
    requester_id: str,
) -> bool:
    """
    Central entry point for any worker that wants to modify a file.

    Parameters
    ----------
    file_path: str
        Absolute or relative path to the target file.
    new_content: str
        The full text that should replace the file's current contents.
    reason: str
        Human‑readable justification for the edit.
    requester_id: str
        Identifier of the worker making the request (e.g., worker name or UUID).

    Returns
    -------
    bool
        ``True`` if the edit was performed, ``False`` otherwise.
    """
    file_name = os.path.basename(file_path)

    # --------------------------------------------------------------
    # NEVER TOUCH tier – hard reject
    # --------------------------------------------------------------
    if _is_never(file_name):
        _log(
            f"DENIED NEVER_TIER edit attempt by {requester_id} on {file_path} "
            f"(reason: {reason})"
        )
        return False

    # --------------------------------------------------------------
    # ASK PERMISSION tier – require reviewer decision
    # --------------------------------------------------------------
    if _is_ask(file_name):
        _log(
            f"ASK_TIER edit request by {requester_id} on {file_path} "
            f"(reason: {reason})"
        )
        if not _reviewer_evaluate(reason, requester_id):
            _log(
                f"DENIED ASK_TIER edit after review by {requester_id} on {file_path}"
            )
            return False

    # --------------------------------------------------------------
    # OPEN tier or approved ASK tier – perform the edit
    # --------------------------------------------------------------
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        _log(f"SUCCESS edit by {requester_id} on {file_path}")
        return True
    except Exception as exc:
        _log(
            f"ERROR writing to {file_path} by {requester_id}: {type(exc).__name__}: {exc}"
        )
        return False
"""
file_permission_gateway.py

Provides a tiered file‑permission system for self‑modifying workers.

Usage Example
-------------
```python
from file_permission_gateway import request_edit, PermissionDeniedError

try:
    with request_edit(
        worker_id="smart_executor",
        file_path="smart_executor.py",
        reason="Add caching layer to improve latency."
    ) as edit:
        # perform the edit here
        edit.apply(lambda: open("smart_executor.py", "a").write("# caching added"))
except PermissionDeniedError as e:
    print(e)
```
"""

import enum
import datetime
import json
import os
import threading
from pathlib import Path
from typing import Callable, List, Optional

# --------------------------------------------------------------------------- #
# Tier definitions
# --------------------------------------------------------------------------- #
class Tier(enum.Enum):
    NEVER = "never"
    ASK = "ask"
    OPEN = "open"


# --------------------------------------------------------------------------- #
# Registry of files per tier
# --------------------------------------------------------------------------- #
# Absolute protection – never editable
NEVER_TIER_FILES = {
    "safety_gateway.py",
    "safety_constitutional.py",
    # add any additional safety files here
}

# Ask‑permission tier – requires reviewer approval
ASK_TIER_FILES = {
    "smart_executor.py",
    "inference_engine.py",
    # extend as needed
}


def _normalize_path(file_path: str) -> str:
    """Return a normalized, case‑insensitive path string."""
    return str(Path(file_path).as_posix()).lower()


def get_tier(file_path: str) -> Tier:
    """Determine the permission tier for a given file."""
    norm = _normalize_path(file_path)
    if any(norm.endswith(_normalize_path(p)) for p in NEVER_TIER_FILES):
        return Tier.NEVER
    if any(norm.endswith(_normalize_path(p)) for p in ASK_TIER_FILES):
        return Tier.ASK
    return Tier.OPEN


# --------------------------------------------------------------------------- #
# Simple thread‑safe logger
# --------------------------------------------------------------------------- #
_LOG_LOCK = threading.Lock()
_LOG_FILE = Path("file_permission.log")


def _log_entry(entry: dict) -> None:
    """Append a JSON line to the log file in a thread‑safe way."""
    with _LOG_LOCK:
        with _LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def log_attempt(
    worker_id: str,
    file_path: str,
    tier: Tier,
    reason: str,
    granted: bool,
    details: Optional[str] = None,
) -> None:
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "worker_id": worker_id,
        "file_path": file_path,
        "tier": tier.value,
        "reason": reason,
        "granted": granted,
        "details": details,
    }
    _log_entry(entry)


# --------------------------------------------------------------------------- #
# Reviewer implementation (can be swapped out for a more sophisticated AI)
# --------------------------------------------------------------------------- #
class ReviewDecision(enum.Enum):
    APPROVE = "approve"
    DENY = "deny"


class Reviewer:
    """
    Independent reviewer that evaluates edit requests.

    The default implementation uses a very simple heuristic:
    - If the reason contains the word "experiment" or "test", approve.
    - Otherwise, deny unless the requester explicitly states "critical improvement".
    """

    @staticmethod
    def evaluate(
        worker_id: str, file_path: str, reason: str
    ) -> ReviewDecision:
        lowered = reason.lower()
        if "experiment" in lowered or "test" in lowered:
            return ReviewDecision.APPROVE
        if "critical improvement" in lowered:
            return ReviewDecision.APPROVE
        return ReviewDecision.DENY


# --------------------------------------------------------------------------- #
# Permission request context manager
# --------------------------------------------------------------------------- #
class PermissionDeniedError(Exception):
    """Raised when a permission request is denied."""


class _EditContext:
    """
    Context manager handed to the caller when permission is granted.
    Provides a single `apply` method to perform the edit atomically.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self._applied = False

    def apply(self, edit_callable: Callable[[], None]) -> None:
        """
        Execute the provided callable that performs the actual file edit.

        The callable should raise its own exceptions on failure; they will
        propagate to the caller.
        """
        if self._applied:
            raise RuntimeError("Edit already applied.")
        edit_callable()
        self._applied = True


def request_edit(
    worker_id: str,
    file_path: str,
    reason: str,
) -> _EditContext:
    """
    Request permission to edit a file.

    Parameters
    ----------
    worker_id: str
        Identifier of the requesting worker.
    file_path: str
        Path to the target file.
    reason: str
        Explanation why the edit is needed.

    Returns
    -------
    _EditContext
        A context manager that must be used with a ``with`` statement.
        Inside the block, call ``edit.apply(lambda: ...)`` to perform the edit.

    Raises
    ------
    PermissionDeniedError
        If the request is denied (either by tier rules or reviewer).
    """
    tier = get_tier(file_path)

    # NEVER tier – auto‑reject
    if tier is Tier.NEVER:
        log_attempt(
            worker_id,
            file_path,
            tier,
            reason,
            granted=False,
            details="File is in NEVER tier.",
        )
        raise PermissionDeniedError(
            f"Edit denied: {file_path} is protected (NEVER tier)."
        )

    # OPEN tier – auto‑grant
    if tier is Tier.OPEN:
        log_attempt(
            worker_id,
            file_path,
            tier,
            reason,
            granted=True,
            details="Open tier – no review needed.",
        )
        return _EditContext(file_path)

    # ASK tier – invoke reviewer workflow
    decision = Reviewer.evaluate(worker_id, file_path, reason)
    if decision is ReviewDecision.APPROVE:
        log_attempt(
            worker_id,
            file_path,
            tier,
            reason,
            granted=True,
            details="Reviewer approved.",
        )
        return _EditContext(file_path)
    else:
        log_attempt(
            worker_id,
            file_path,
            tier,
            reason,
            granted=False,
            details="Reviewer denied.",
        )
        raise PermissionDeniedError(
            f"Edit denied by reviewer for {file_path} (ASK tier)."
        )
\"\"\"file_permission_gateway.py
A lightweight permission gateway that enforces the three‑tier policy
described in FILE_PERMISSION_TIERS.md.

Usage example:

```python
from file_permission_gateway import PermissionGateway, require_permission

@gateway.require_permission
def edit_smart_executor(new_code: str):
    with open("smart_executor.py", "w") as f:
        f.write(new_code)
```

The gateway will:
* Identify the tier of the target file.
* For ASK‑PERMISSION files, request a justification, invoke a reviewer,
  and either allow or deny the edit.
* Log every attempt for auditability.
\"\"\"

import os
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

# ----------------------------------------------------------------------
# Tier definitions (order matters for pattern matching)
# ----------------------------------------------------------------------
_NEVER_TIER_PATTERNS = [
    "safety_*.py",
    "grind_spawner*.py",
    "orchestrator.py",
    "roles.py",
    "groq_code_extractor.py",
    "surgical_edit_extractor.py",
]

_ASK_TIER_PATTERNS = [
    "smart_executor.py",
    "inference_engine.py",
]

# ----------------------------------------------------------------------
# Simple thread‑safe logger
# ----------------------------------------------------------------------
_log_lock = threading.Lock()
_LOG_FILE = Path("file_permission_log.json")

def _append_log(entry: dict) -> None:
    with _log_lock:
        logs = []
        if _LOG_FILE.exists():
            try:
                logs = json.loads(_LOG_FILE.read_text())
            except Exception:
                logs = []
        logs.append(entry)
        _LOG_FILE.write_text(json.dumps(logs, indent=2))

# ----------------------------------------------------------------------
# Reviewer stub – replace with a real reviewer (human, LLM, etc.)
# ----------------------------------------------------------------------
class Reviewer:
    \"\"\"Stateless reviewer used for the ASK‑PERMISSION tier.

    The default implementation is deliberately simple:
    * If the justification length is >= 15 characters → approve.
    * Otherwise → deny.

    Override :meth:`evaluate` with your own logic.
    \"\"\"

    @staticmethod
    def evaluate(requester: str, file_path: str, reason: str) -> bool:
        # Placeholder logic – can be replaced with a more sophisticated reviewer.
        return len(reason.strip()) >= 15

# ----------------------------------------------------------------------
# Permission gateway implementation
# ----------------------------------------------------------------------
class PermissionGateway:
    \"\"\"Core gateway handling permission checks and logging.\"\"\"

    def __init__(self):
        self.reviewer = Reviewer()

    # ------------------------------------------------------------------
    # Tier detection
    # ------------------------------------------------------------------
    @staticmethod
    def _matches_pattern(path: str, pattern: str) -> bool:
        # Convert simple glob‑style pattern to a regex‑compatible match
        from fnmatch import fnmatch
        return fnmatch(os.path.basename(path), pattern)

    def get_tier(self, file_path: str) -> str:
        \"\"\"Return one of: ``'never'``, ``'ask'``, ``'open'``.\"
        \"\"\"
        # Never‑touch overrides everything
        for pat in _NEVER_TIER_PATTERNS:
            if self._matches_pattern(file_path, pat):
                return "never"

        for pat in _ASK_TIER_PATTERNS:
            if self._matches_pattern(file_path, pat):
                return "ask"

        return "open"

    # ------------------------------------------------------------------
    # Core request handling
    # ------------------------------------------------------------------
    def request_edit(
        self,
        requester: str,
        file_path: str,
        reason: str,
        *,
        auto_approve: Optional[bool] = None,
    ) -> bool:
        \"\"\"Process an edit request.

        Parameters
        ----------
        requester: str
            Identifier of the worker making the request.
        file_path: str
            Target file to be edited.
        reason: str
            Explanation *why* the edit is needed.
        auto_approve: Optional[bool]
            If set, bypasses the reviewer and forces the decision
            (useful for tests).

        Returns
        -------
        bool
            ``True`` if the edit is permitted, ``False`` otherwise.
        \"\"\"
        tier = self.get_tier(file_path)
        timestamp = datetime.utcnow().isoformat() + "Z"

        # ------------------------------------------------------------------
        # NEVER tier – hard block
        # ------------------------------------------------------------------
        if tier == "never":
            _append_log({
                "timestamp": timestamp,
                "requester": requester,
                "file": file_path,
                "tier": tier,
                "decision": "denied",
                "reason": "attempt to modify never‑touch file",
                "justification": reason,
            })
            return False

        # ------------------------------------------------------------------
        # OPEN tier – free edit
        # ------------------------------------------------------------------
        if tier == "open":
            _append_log({
                "timestamp": timestamp,
                "requester": requester,
                "file": file_path,
                "tier": tier,
                "decision": "granted",
                "reason": "open tier – no restrictions",
                "justification": reason,
            })
            return True

        # ------------------------------------------------------------------
        # ASK tier – go through reviewer
        # ------------------------------------------------------------------
        # Record the request before evaluation for full audit trail
        decision = None
        if auto_approve is not None:
            decision = auto_approve
        else:
            try:
                decision = self.reviewer.evaluate(requester, file_path, reason)
            except Exception as exc:
                # Any reviewer failure is treated as a denial for safety
                decision = False
                reason = f"Reviewer error: {exc}"

        _append_log({
            "timestamp": timestamp,
            "requester": requester,
            "file": file_path,
            "tier": tier,
            "decision": "granted" if decision else "denied",
            "reason": reason,
            "justification": reason,
        })
        return decision

    # ------------------------------------------------------------------
    # Decorator for easy integration
    # ------------------------------------------------------------------
    def require_permission(self, func: Callable) -> Callable:
        \"\"\"Decorator that enforces permission before executing *func*.

        The wrapped function must accept ``file_path`` as a keyword
        argument (or positional argument named ``file_path``) and may
        optionally accept ``requester`` and ``reason`` keyword arguments.
        \"\"\"

        def wrapper(*args, **kwargs):
            file_path = kwargs.get("file_path")
            if not file_path:
                # Attempt to infer from positional args (first str argument)
                for a in args:
                    if isinstance(a, str) and os.path.isfile(a):
                        file_path = a
                        break
            if not file_path:
                raise ValueError("file_path not supplied to permission‑guarded function")

            requester = kwargs.get("requester", "unknown_worker")
            reason = kwargs.get("reason", "")

            if not self.request_edit(requester, file_path, reason):
                # Permission denied – raise a clear exception
                raise PermissionError(
                    f"Edit to '{file_path}' denied by permission gateway (tier: {self.get_tier(file_path)})"
                )
            # Permission granted – proceed with original function
            return func(*args, **kwargs)

        return wrapper


# ----------------------------------------------------------------------
# Instantiate a module‑level gateway for import convenience
# ----------------------------------------------------------------------
gateway = PermissionGateway()
\"\"\"file_permission_gateway.py
A lightweight, import‑ready module that enforces the tiered file‑permission system
described in FILE_PERMISSION_TIERS.md.

Key public API:
    - `Tier` (Enum): NEVER, ASK, OPEN
    - `get_tier(file_path: str) -> Tier`
    - `request_edit(requester: str, file_path: str, reason: str,
                    reviewer: Callable[[str, str, str], bool] | None = None) -> bool`

The default reviewer is a simple console prompt, but callers can supply any
callable that returns a boolean decision.
\"\"\"

import fnmatch
import logging
import os
import threading
from datetime import datetime
from enum import Enum
from typing import Callable, Optional

# --------------------------------------------------------------------------- #
# Logging configuration – a single file shared across workers (thread‑safe)
# --------------------------------------------------------------------------- #
LOG_FILE = os.path.abspath("edit_attempts.log")
_log_lock = threading.Lock()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)


# --------------------------------------------------------------------------- #
# Tier definition
# --------------------------------------------------------------------------- #
class Tier(Enum):
    NEVER = "never"
    ASK = "ask"
    OPEN = "open"


# --------------------------------------------------------------------------- #
# Tier mapping – patterns are evaluated in order; first match wins
# --------------------------------------------------------------------------- #
_TIER_PATTERNS = [
    # NEVER tier – safety‑critical files
    (Tier.NEVER, "safety_*.py"),
    (Tier.NEVER, "safety_gateway.py"),
    (Tier.NEVER, "safety_constitutional.py"),
    # ASK tier – core logic that may evolve
    (Tier.ASK, "*_executor.py"),
    (Tier.ASK, "*_engine.py"),
    (Tier.ASK, "smart_executor.py"),
    (Tier.ASK, "inference_engine.py"),
    # OPEN tier – fallback for everything else
    (Tier.OPEN, "*"),
]


def _match_tier(file_path: str) -> Tier:
    """Return the first matching tier for *file_path*."""
    filename = os.path.basename(file_path)
    for tier, pattern in _TIER_PATTERNS:
        if fnmatch.fnmatch(filename, pattern):
            return tier
    # Should never reach here because of the final OPEN wildcard
    return Tier.OPEN


def get_tier(file_path: str) -> Tier:
    \"\"\"Public helper to expose the tier of a given file."""
    return _match_tier(file_path)


# --------------------------------------------------------------------------- #
# Default reviewer – simple console interaction
# --------------------------------------------------------------------------- #
def _default_reviewer(requester: str, file_path: str, reason: str) -> bool:
    """
    Prompt the reviewer (via stdin) to approve or deny the edit.
    Returns True if approved, False otherwise.
    """
    print("\n--- EDIT REQUEST ---")
    print(f"Requester : {requester}")
    print(f"File      : {file_path}")
    print(f"Reason    : {reason}")
    while True:
        resp = input("Approve edit? (y/n): ").strip().lower()
        if resp in {"y", "yes"}:
            return True
        if resp in {"n", "no"}:
            return False
        print("Please answer 'y' or 'n'.")


# --------------------------------------------------------------------------- #
# Core permission request function
# --------------------------------------------------------------------------- #
def request_edit(
    requester: str,
    file_path: str,
    reason: str,
    reviewer: Optional[Callable[[str, str, str], bool]] = None,
) -> bool:
    """
    Main entry point for a worker that wants to modify *file_path*.

    Parameters
    ----------
    requester: str
        Identifier of the worker making the request.
    file_path: str
        Path to the target file (relative or absolute).
    reason: str
        Human‑readable justification for the edit.
    reviewer: Callable or None
        Optional custom reviewer. If None, the built‑in console reviewer is used.

    Returns
    -------
    bool
        True if the edit is permitted, False otherwise.
    """
    tier = get_tier(file_path)

    # ------------------------------------------------------------------- #
    # NEVER tier – outright block
    # ------------------------------------------------------------------- #
    if tier is Tier.NEVER:
        msg = f"EDIT BLOCKED (NEVER tier) – {requester} attempted to modify {file_path}"
        with _log_lock:
            logging.warning(msg)
        return False

    # ------------------------------------------------------------------- #
    # OPEN tier – automatically allow
    # ------------------------------------------------------------------- #
    if tier is Tier.OPEN:
        msg = f"EDIT ALLOWED (OPEN tier) – {requester} will edit {file_path}"
        with _log_lock:
            logging.info(msg)
        return True

    # ------------------------------------------------------------------- #
    # ASK tier – require reviewer decision
    # ------------------------------------------------------------------- #
    # Use provided reviewer or fall back to the default console reviewer
    reviewer_func = reviewer or _default_reviewer

    # Log the request before asking the reviewer (audit trail)
    request_log = (
        f"EDIT REQUEST (ASK tier) – requester: {requester}, file: {file_path}, reason: {reason}"
    )
    with _log_lock:
        logging.info(request_log)

    try:
        approved = reviewer_func(requester, file_path, reason)
    except Exception as exc:
        # Any reviewer error is treated as a denial and logged
        err_msg = f"REVIEWER ERROR – {exc!r}; treating as denial for {file_path}"
        with _log_lock:
            logging.error(err_msg)
        approved = False

    # Record the outcome
    outcome = "GRANTED" if approved else "DENIED"
    outcome_msg = f"EDIT {outcome} – requester: {requester}, file: {file_path}"
    with _log_lock:
        logging.info(outcome_msg)

    return approved


# --------------------------------------------------------------------------- #
# Convenience decorator for functions that perform file writes
# --------------------------------------------------------------------------- #
def requires_permission(func):
    """
    Decorator that checks permission before executing a function that writes
    to a file. The wrapped function must accept the following keyword arguments:

        * requester (str)
        * file_path (str)
        * reason (str)

    If permission is denied, the function returns without calling the original.
    """
    def wrapper(*args, **kwargs):
        requester = kwargs.get("requester")
        file_path = kwargs.get("file_path")
        reason = kwargs.get("reason", "No reason supplied")
        if not requester or not file_path:
            raise ValueError("Decorator requires 'requester' and 'file_path' kwargs.")
        if request_edit(requester, file_path, reason):
            return func(*args, **kwargs)
        # Permission denied – no operation performed
        return None
    return wrapper