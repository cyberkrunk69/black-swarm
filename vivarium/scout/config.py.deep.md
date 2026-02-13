# config.py

## Function: `_path_matches`

Detailed documentation (deep stub).

```python
def _path_matches(path: Path, pattern: str) -> bool:
    """
    Match path against glob pattern (supports * and **).
    * = any chars except /; ** = any number of path segments.
    """
    path_str = str(path).replace("\\", "/")
    pattern = pattern.replace("\\", "/")
    # Convert glob to regex: * -> [^/]*, ** -> (?:[^/]+/)*[^/]*
    # Escaped, then * -> [^/]*, ? -> ., ** -> .*
    def _glob_to_regex(p: str) -> str:
        i = 0
        result = []
        while i < len(p):
            if 
```

## Class: `TriggerConfig`

Detailed documentation (deep stub).

```python
class TriggerConfig:
    """Resolved trigger type and cost limit for a file path."""

    type: str  # manual | on-save | on-commit | on-push | disabled
    max_cost: float
```

## Function: `_deep_merge`

Detailed documentation (deep stub).

```python
def _deep_merge(base: dict, override: dict) -> dict:
    """Merge override into base recursively. Override wins."""
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result
```

## Function: `_load_yaml`

Detailed documentation (deep stub).

```python
def _load_yaml(path: Path) -> Optional[dict]:
    """Load YAML file. Return None if missing or invalid."""
    if not path.exists():
        return None
    try:
        import yaml

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else None
    except Exception as e:
        logger.warning("ScoutConfig: failed to load %s: %s", path, e)
        return None
```

## Function: `_save_yaml`

Detailed documentation (deep stub).

```python
def _save_yaml(path: Path, data: dict) -> bool:
    """Save dict to YAML. Return True on success."""
    try:
        import yaml

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        logger.warning("ScoutConfig: failed to save %s: %s", path, e)
        return False
```

## Function: `_get_nested`

Detailed documentation (deep stub).

```python
def _get_nested(data: dict, *keys: str) -> Any:
    """Get nested key. Returns None if any key missing."""
    cur = data
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur
```

## Function: `_set_nested`

Detailed documentation (deep stub).

```python
def _set_nested(data: dict, value: Any, *keys: str) -> None:
    """Set nested key, creating dicts as needed."""
    for k in keys[:-1]:
        if k not in data or not isinstance(data[k], dict):
            data[k] = {}
        data = data[k]
    data[keys[-1]] = value
```

## Class: `ScoutConfig`

Detailed documentation (deep stub).

```python
class ScoutConfig:
    """
    Layered configuration: user YAML + env vars + hard caps.

    Hard caps are never overridden by user config.
    """

    def __init__(self, search_paths: Optional[List[Path]] = None):
        """
        Load config with precedence order:
        1. Hardcoded defaults
        2. ~/.scout/config.yaml (user global)
        3. .scout/config.yaml (project local)
        4. Environment variables
        """
        self._raw: Dict[str, Any] = dict(DEFAULT_CONFIG)
     
```

## Function: `_glob_to_regex`

Detailed documentation (deep stub).

```python
    def _glob_to_regex(p: str) -> str:
        i = 0
        result = []
        while i < len(p):
            if i + 1 < len(p) and p[i : i + 2] == "**":
                # ** = zero or more path segments: (?:[^/]+/)*[^/]*
                result.append("(?:[^/]+/)*[^/]*")
                i += 2
            elif p[i] == "*":
                result.append("[^/]*")
                i += 1
            elif p[i] == "?":
                result.append(".")
                i += 1
            else:
      
```

## Function: `__init__`

Detailed documentation (deep stub).

```python
    def __init__(self, search_paths: Optional[List[Path]] = None):
        """
        Load config with precedence order:
        1. Hardcoded defaults
        2. ~/.scout/config.yaml (user global)
        3. .scout/config.yaml (project local)
        4. Environment variables
        """
        self._raw: Dict[str, Any] = dict(DEFAULT_CONFIG)
        paths = (
            self._default_search_paths()
            if search_paths is None
            else list(search_paths)
        )
        for p
```

## Function: `_default_search_paths`

Detailed documentation (deep stub).

```python
    def _default_search_paths(self) -> List[Path]:
        """Return [user_global, project_local] paths."""
        user = Path.home() / ".scout" / "config.yaml"
        project = Path.cwd() / ".scout" / "config.yaml"
        return [user, project]
```

## Function: `_apply_env_overrides`

Detailed documentation (deep stub).

```python
    def _apply_env_overrides(self) -> None:
        """Apply env vars over config."""
        for env_key, (section, key, conv) in ENV_TO_CONFIG.items():
            val = os.environ.get(env_key)
            if val is None:
                continue
            try:
                if conv is float:
                    parsed = float(val)
                elif conv is str:
                    parsed = str(val).strip()
                else:
                    parsed = val
                if sectio
```

## Function: `_ensure_hard_cap_in_limits`

Detailed documentation (deep stub).

```python
    def _ensure_hard_cap_in_limits(self) -> None:
        """Ensure limits.hard_safety_cap reflects the constant (informational)."""
        limits = self._raw.get("limits") or {}
        limits["hard_safety_cap"] = HARD_MAX_HOURLY_BUDGET  # Non-overridable
        self._raw["limits"] = limits
```

## Function: `resolve_trigger`

Detailed documentation (deep stub).

```python
    def resolve_trigger(self, file_path: Path) -> TriggerConfig:
        """
        Return trigger type and cost limit for this file.
        First pattern match wins; else fall back to default.
        """
        path_str = str(Path(file_path).as_posix())
        patterns = self._raw.get("triggers", {}).get("patterns") or []
        for entry in patterns:
            pattern = entry.get("pattern", "")
            if not pattern:
                continue
            if _path_matches(Path(path_
```

## Function: `effective_max_cost`

Detailed documentation (deep stub).

```python
    def effective_max_cost(self, file_path: Optional[Path] = None) -> float:
        """
        User setting bounded by hard safety cap.
        """
        if file_path is not None:
            path_str = str(Path(file_path).as_posix())
            patterns = self._raw.get("triggers", {}).get("patterns") or []
            for entry in patterns:
                if _path_matches(Path(path_str), entry.get("pattern", "")):
                    mc = entry.get("max_cost")
                    if mc is
```

## Function: `should_process`

Detailed documentation (deep stub).

```python
    def should_process(
        self,
        estimated_cost: float,
        file_path: Optional[Path] = None,
        hourly_spend: float = 0.0,
    ) -> bool:
        """
        Check all limits before any LLM call.
        Returns True only if estimated_cost fits within per-event and hourly budgets.
        """
        max_per = self.effective_max_cost(file_path)
        if estimated_cost > max_per:
            return False
        if estimated_cost > HARD_MAX_COST_PER_EVENT:
            ret
```

## Function: `to_dict`

Detailed documentation (deep stub).

```python
    def to_dict(self) -> dict:
        """Current effective config (for audit logging)."""
        return {
            "triggers": dict(self._raw.get("triggers", {})),
            "limits": dict(self._raw.get("limits", {})),
            "models": dict(self._raw.get("models", {})),
            "notifications": dict(self._raw.get("notifications", {})),
            "hard_caps": {
                "max_cost_per_event": HARD_MAX_COST_PER_EVENT,
                "hourly_budget": HARD_MAX_HOURLY_BUDGET,
```

## Function: `get_user_config_path`

Detailed documentation (deep stub).

```python
    def get_user_config_path(self) -> Path:
        """Path to user global config (for opening in editor)."""
        return Path.home() / ".scout" / "config.yaml"
```

## Function: `get_project_config_path`

Detailed documentation (deep stub).

```python
    def get_project_config_path(self) -> Path:
        """Path to project local config."""
        return Path.cwd() / ".scout" / "config.yaml"
```

## Function: `get`

Detailed documentation (deep stub).

```python
    def get(self, key_path: str) -> Optional[Any]:
        """Get value by dot path, e.g. 'triggers.default'."""
        parts = key_path.split(".")
        return _get_nested(self._raw, *parts)
```

## Function: `set`

Detailed documentation (deep stub).

```python
    def set(self, key_path: str, value: Any) -> bool:
        """Set value by dot path. Writes to project config if it exists."""
        parts = key_path.split(".")
        if len(parts) < 2:
            return False
        _set_nested(self._raw, value, *parts)
        proj = self.get_project_config_path()
        if proj.exists():
            return _save_yaml(proj, self._raw)
        user = self.get_user_config_path()
        user.parent.mkdir(parents=True, exist_ok=True)
        return _sav
```

## Function: `validate_yaml`

Detailed documentation (deep stub).

```python
    def validate_yaml(self, path: Optional[Path] = None) -> tuple[bool, str]:
        """
        Validate YAML syntax. Returns (ok, message).
        If path is None, validates merged config.
        """
        if path is not None:
            try:
                import yaml

                with open(path, encoding="utf-8") as f:
                    yaml.safe_load(f)
                return True, "Valid YAML"
            except Exception as e:
                return False, str(e)
        # Va
```
