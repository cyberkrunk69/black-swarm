# llm.py

## Class: `NavResponse`

Detailed documentation (deep stub).

```python
class NavResponse:
    """Raw LLM response for navigation."""

    content: str
    cost_usd: float
    model: str
    input_tokens: int
    output_tokens: int
```

## Function: `_get_groq_api_key`

Detailed documentation (deep stub).

```python
def _get_groq_api_key() -> Optional[str]:
    """Get Groq API key from env or runtime config."""
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key
    try:
        from vivarium.runtime import config as runtime_config

        return runtime_config.get_groq_api_key()
    except ImportError:
        return None
```

## Function: `call_groq_async`

Detailed documentation (deep stub).

```python
async def call_groq_async(
    prompt: str,
    model: str = "llama-3.1-8b-instant",
    system: Optional[str] = None,
    llm_client: Optional[Callable] = None,
) -> NavResponse:
    """
    Call Groq API for navigation. Uses llm_client if provided (for testing).
    """
    if llm_client:
        return await llm_client(prompt, model=model, system=system)

    api_key = _get_groq_api_key()
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY not set. Set it in environment 
```
