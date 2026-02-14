<!-- FACT_CHECKSUM: 31301cabac224d96b96fa75a179548a506ae40858939d0dbf4b5a74915a1cd94 -->

# ELIV
This module coordinates specialized helpers with awareness of constraints and activity.

## Constants
### `_COMPLEXITY_KEYWORDS`

* Value: `['algorithm', 'optimize', 'refactor', 'benchmark', 'scale', 'performance', 'thread', 'process', 'async', 'concurrency', 'distributed', 'pipeline', 'sql', 'database', 'api', 'authentication', 'encryption', 'docker', 'kubernetes', 'microservice', 'cache', 'index', 'migration']`
* Type: `List[str]`
* Semantic role: implementation
* Used at lines: 66

## Methods
### `EngineType`

* Docstring: Available inference backends.
* Semantic role: implementation
* Used at lines: 76, 81, 83, 84

### `estimate_complexity`

* Docstring: Return a numeric complexity score. Higher scores -> more demanding request.
    Scoring factors:
    - Base score = token count // 10
    - +2 for each recognized complexity keyword present
    - +5 ...
* Signature: `def estimate_complexity(request: str) -> int`
* Semantic role: implementation
* Used at lines: (none)

### `get_engine_type_from_env`

* Docstring: Determine engine type from INFERENCE_ENGINE environment variable.
* Signature: `def get_engine_type_from_env() -> EngineType`
* Semantic role: implementation
* Used at lines: (none)