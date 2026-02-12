# Scout Audit Schema

Scout uses an append-only JSONL event log for accounting and debugging. Every line is valid JSON.

## Location

Default: `~/.scout/audit.jsonl`  
Configurable via `AuditLog(path=...)`.

## Common Fields (all events)

| Field        | Type   | Required | Description                                      |
|--------------|--------|----------|--------------------------------------------------|
| `ts`         | string | Yes      | ISO8601 with millis, UTC (e.g. `2026-02-13T14:30:22.123Z`) |
| `event`      | string | Yes      | Event type (see below)                           |
| `session_id` | string | Yes      | UUID4 per process                                |

## Event Types

| Event              | Description                                           |
|--------------------|-------------------------------------------------------|
| `nav`              | Navigation suggestion offered                         |
| `brief`            | Brief/summary generated                               |
| `cascade`          | Cascade/chain event                                   |
| `validation_fail`  | Zero-cost validation failed (e.g. hallucinated path) |
| `budget`           | Budget-related event (spend, limit)                   |
| `skip`             | Action skipped (cost, threshold)                       |
| `trigger`          | Trigger fired (e.g. on-commit)                        |

## Event-Specific Fields

Include only when relevant:

| Field        | Type     | Events  | Description                             |
|--------------|----------|---------|-----------------------------------------|
| `cost`       | float    | nav, brief, budget | USD cost                      |
| `model`      | string   | nav, brief | Model name (e.g. `llama-3.1-8b`)      |
| `input_t`    | int      | nav, brief | Input token count                    |
| `output_t`   | int      | nav, brief | Output token count                   |
| `files`      | list[str]| nav, brief | Affected file paths                  |
| `reason`     | string   | validation_fail, skip, budget | e.g. `hallucinated_path`, `cost_exceeds_limit`, `hourly_budget_exhausted` |
| `confidence` | int      | nav, brief | 0–100 confidence                     |
| `duration_ms`| int      | any      | Elapsed milliseconds                   |
| `config`     | object   | any      | Config snapshot at event time          |

## Example Lines

```json
{"ts":"2026-02-13T14:30:22.123Z","event":"nav","session_id":"...","cost":0.000003,"model":"llama-3.1-8b","input_t":42,"output_t":28}
{"ts":"2026-02-13T14:30:23.000Z","event":"validation_fail","session_id":"...","reason":"hallucinated_path","files":["path/to/file.py"]}
{"ts":"2026-02-13T14:30:24.000Z","event":"budget","session_id":"...","reason":"hourly_budget_exhausted","config":{"max_cost":0.05,"trigger":"on-commit"}}
```

## Log Rotation

- Auto-archive at 10MB
- Old logs gzipped: `audit_YYYYMMDD_HHMMSS.jsonl.gz`
- Current active log: `audit.jsonl`

## Corruption Recovery

- Malformed lines are skipped on read
- A warning is logged for each skipped line
- Partial last line (e.g. after crash) does not block parsing of prior lines
