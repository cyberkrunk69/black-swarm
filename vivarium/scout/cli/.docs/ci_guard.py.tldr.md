# DEFAULT_BASE_BRANCH

The DEFAULT_BASE_BRANCH constant is not explicitly used in the system.
---

# DEFAULT_HOURLY_SPEND_LIMIT

TL;DR: The DEFAULT_HOURLY_SPEND_LIMIT constant is not directly involved in any system operations, as there are no traced calls or used types. It is imported from the vivarium/scout module, suggesting it may be a configuration or setting used elsewhere in the system.
---

# DEFAULT_MIN_CONFIDENCE

The DEFAULT_MIN_CONFIDENCE constant is not used in any traced calls. It imports modules from vivarium/scout, but its purpose cannot be determined from the provided information.
---

# _check_tldr_coverage

This function checks the coverage of a TL;DR file by comparing its length to the length of the original file. It uses the `vivarium/scout/ignore.py` module to ignore certain patterns and the `vivarium/scout/git_analyzer.py` module to analyze the TL;DR file. It appends errors to a list if the TL;DR file is incomplete.
---

# _check_draft_confidence

This function checks the draft confidence by querying the audit log and appending errors if the draft confidence is not valid. It appears to be part of a system that analyzes Git repositories, possibly to validate or enforce certain configuration or consistency rules. The function likely returns or modifies the draft confidence value based on the audit log query results.
---

# _check_hourly_spend

TL;DR: The _check_hourly_spend function calls audit.hourly_spend and uses AuditLog and float types. It appears to be related to auditing hourly spend, possibly for logging or analysis purposes.
---

# _check_draft_events_recent

This function checks recent draft events by querying the audit log. It uses the current date and time to determine the time frame of recent events. It likely filters out events older than a certain threshold.
---

# run_ci_guard

This function appears to be part of a Continuous Integration (CI) guard, responsible for auditing a repository's changes and spending. It calls various functions to check for draft confidence, recent events, hourly spend, and TLDR coverage, and logs any audit results.
---

# main

This function appears to be a command-line interface (CLI) entry point, utilizing the `argparse` library to parse command-line arguments. It likely performs some form of analysis or validation, possibly related to a Git repository, given the imports from `vivarium/scout/git_analyzer.py`.