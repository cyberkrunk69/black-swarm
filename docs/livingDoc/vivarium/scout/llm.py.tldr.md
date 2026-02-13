# NavResponse

**NavResponse Class Summary**
================================

The `NavResponse` class represents a raw LLM (Large Language Model) response for navigation. Its primary purpose is to encapsulate the output of a navigation-related LLM query, with key responsibilities including storing and managing the response data. It depends on configuration settings from `vivarium/scout/config.py` and utilizes cost functions from `vivarium/utils/llm_cost.py` for navigation-related calculations.
---

# _get_groq_api_key

**Function Summary: `_get_groq_api_key`**

The `_get_groq_api_key` function retrieves a Groq API key from either environment variables or runtime configuration. It handles exceptions and returns the API key as a string. This function depends on configuration settings from `vivarium/scout/config.py` and utilizes functionality from `vivarium/utils/llm_cost.py` and `vivarium/runtime/__init__.py`.
---

# call_groq_async

**call_groq_async Function Summary**
=====================================

The `call_groq_async` function is an asynchronous function that calls the Groq API for navigation. It takes in a prompt and various optional parameters, including a model, system, and maximum tokens, and returns a `NavResponse` object. The function uses the `llm_client` if provided for testing purposes, and depends on configuration and utility functions from `vivarium/scout/config.py` and `vivarium/utils/llm_cost.py`.