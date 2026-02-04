import os
from pathlib import Path
from typing import Any, Dict

try:
    # Prefer python-dotenv if available for .env files
    from dotenv import load_dotenv

    # Load .env from the project root or the experiment folder if present
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.is_file():
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        # Fallback to loading from the experiment folder
        load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)
except ImportError:
    # If python-dotenv is not installed, rely on the OS environment only
    pass


def _cast_value(value: str) -> Any:
    """Attempt to cast environment string values to native Python types."""
    lowered = value.lower()
    if lowered in {"true", "yes", "1"}:
        return True
    if lowered in {"false", "no", "0"}:
        return False
    try:
        # Integer conversion
        return int(value)
    except ValueError:
        pass
    try:
        # Float conversion
        return float(value)
    except ValueError:
        pass
    return value  # Return as string if no conversion succeeded


def get_config(key: str, default: Any = None) -> Any:
    """
    Retrieve a configuration value from the environment.

    Parameters
    ----------
    key : str
        The environment variable name.
    default : Any, optional
        Value to return if the variable is not set.

    Returns
    -------
    Any
        The casted environment value or the default.
    """
    raw = os.getenv(key, default)
    if raw is None:
        return None
    if isinstance(raw, str):
        return _cast_value(raw)
    return raw


def load_all(prefix: str = "") -> Dict[str, Any]:
    """
    Load all environment variables optionally filtered by a prefix.

    Parameters
    ----------
    prefix : str, optional
        If provided, only variables that start with this prefix are returned,
        with the prefix stripped from the keys.

    Returns
    -------
    dict
        Mapping of configuration keys to their casted values.
    """
    config: Dict[str, Any] = {}
    for key, value in os.environ.items():
        if prefix:
            if not key.startswith(prefix):
                continue
            clean_key = key[len(prefix) :].lstrip("_")
        else:
            clean_key = key
        config[clean_key] = _cast_value(value)
    return config


# Example usage (can be removed in production)
if __name__ == "__main__":
    # Print all config values for debugging
    import json

    print(json.dumps(load_all(), indent=2))