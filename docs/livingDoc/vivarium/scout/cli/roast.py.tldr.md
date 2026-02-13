# PERIOD_TODAY

The Python constant 'PERIOD_TODAY' is not explicitly defined in the provided information. However, based on the context, it is likely related to a time period constant used in the vivarium/scout/audit.py, vivarium/scout/config.py, or vivarium/scout/llm.py modules.

It is used to represent a time period, specifically today, and is likely used for date-based calculations or filtering in the scout module.
---

# PERIOD_WEEK

The Python constant 'PERIOD_WEEK' is not explicitly defined in the provided information. However, based on the vivarium/scout/audit.py, vivarium/scout/config.py, and vivarium/scout/llm.py dependencies, it is likely related to time period constants used in the vivarium/scout library.

It is used to represent a week-long time period, possibly for scheduling or simulation purposes.
---

# PERIOD_MONTH

The Python constant 'PERIOD_MONTH' is not explicitly documented, but based on its interactions with other modules, it likely represents a time period in months. Its primary purpose is to define a time unit for calculations or comparisons. It depends on the vivarium/scout/audit.py, vivarium/scout/config.py, and vivarium/scout/llm.py modules for its functionality.
---

# DEFAULT_NAIVE_COST_PER_NAV

The `DEFAULT_NAIVE_COST_PER_NAV` constant is not explicitly documented, but based on its interactions with `vivarium/scout/audit.py`, `vivarium/scout/config.py`, and `vivarium/scout/llm.py`, it appears to represent a default cost value for navigation in a simulation or model. Its primary purpose is to provide a baseline cost for navigation, and it likely influences the behavior of the dependencies listed above.
---

# _parse_archive_timestamp

**_parse_archive_timestamp Function Summary**
=============================================

The `_parse_archive_timestamp` function parses a timestamp from a given archive file name and returns it as a datetime object in UTC. It handles exceptions and depends on the `vivarium/scout/audit.py` and `vivarium/scout/config.py` modules for configuration and timestamp parsing.
---

# _iter_archive_lines

**_iter_archive_lines Function Summary**
=====================================

The `_iter_archive_lines` function yields non-empty lines from a gzipped JSONL archive. It iterates over the archive, handling exceptions and filtering out empty lines. The function depends on the `vivarium/scout/audit.py`, `vivarium/scout/config.py`, and `vivarium/scout/llm.py` modules for its functionality.
---

# load_audit_log

**load_audit_log Function Summary**
=====================================

The `load_audit_log` function loads audit events for a specified period from current and archived logs. It takes a `period` parameter and an optional `audit_path` parameter, and returns a sorted list of events with timestamps greater than or equal to the start of the period.

It interacts with `vivarium/scout/audit.py`, `vivarium/scout/config.py`, and `vivarium/scout/llm.py` to load and process audit logs.
---

# calculate_accuracy

**calculate_accuracy Function Summary**
=====================================

The `calculate_accuracy` function computes accuracy metrics from a list of events, including total navigation, validation failure count, and accuracy percentage. It relies on external dependencies from `vivarium/scout/audit.py`, `vivarium/scout/config.py`, and `vivarium/scout/llm.py` to perform its calculations.
---

# generate_report

**generate_report Function Summary**
=====================================

The `generate_report` function generates a roast report from audit events, calculating key metrics such as scout cost, naive cost, savings, and accuracy. It depends on the `vivarium/scout/audit.py`, `vivarium/scout/config.py`, and `vivarium/scout/llm.py` modules to perform its calculations.
---

# _load_docs_for_file

**Function Summary: `_load_docs_for_file`**

Loads documentation files for a given file path, searching in `.docs/` and `docs/livingDoc/` directories within the repository root. It returns the loaded documentation as a string, handling exceptions and dependencies from `vivarium/scout/audit.py`, `vivarium/scout/config.py`, and `vivarium/scout/llm.py`.
---

# _run_roast

**Function Summary: `_run_roast`**

The `_run_roast` function runs a Large Language Model (LLM) critique on target files, injecting summary and deep dive documents if `use_docs` is True. It respects the `enable_roast` configuration and logs an audit event. The function interacts with `vivarium/scout/audit.py`, `vivarium/scout/config.py`, and `vivarium/scout/llm.py` to perform its tasks.
---

# format_report

**Format Report Function Summary**

The `format_report` function formats a roast report as an ASCII box based on the provided data. It takes a dictionary of data as input and returns a formatted string. The function likely uses conditional statements and function calls to process the data from dependencies such as `vivarium/scout/audit.py`, `vivarium/scout/config.py`, and `vivarium/scout/llm.py`.
---

# main

**Main Function Summary**
==========================

The `main` function serves as the CLI entry point, responsible for executing the primary logic of the application. It conditionally performs tasks and returns an integer value. The function interacts with dependencies from `vivarium/scout/audit.py`, `vivarium/scout/config.py`, and `vivarium/scout/llm.py` to fulfill its purpose.