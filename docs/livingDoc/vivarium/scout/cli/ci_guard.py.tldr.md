# DEFAULT_BASE_BRANCH

The `DEFAULT_BASE_BRANCH` constant is not explicitly documented, but based on its interactions with other modules, it appears to be a default base branch name used in the vivarium/scout package. Its primary purpose is to provide a default value for base branch operations, and it is likely used in conjunction with `vivarium/scout/audit.py`, `vivarium/scout/git_analyzer.py`, and `vivarium/scout/ignore.py` to manage branch-related tasks.
---

# DEFAULT_HOURLY_SPEND_LIMIT

The `DEFAULT_HOURLY_SPEND_LIMIT` constant is not explicitly documented, but based on its name and interactions with other modules, it likely represents the default hourly spend limit for a project or resource. Its primary purpose is to set a threshold for hourly resource usage, and it may be used in conjunction with the `vivarium/scout/audit.py`, `vivarium/scout/git_analyzer.py`, and `vivarium/scout/ignore.py` modules to monitor and manage resource utilization.
---

# DEFAULT_MIN_CONFIDENCE

**DEFAULT_MIN_CONFIDENCE**
==========================

The `DEFAULT_MIN_CONFIDENCE` constant is not explicitly documented, but based on its interactions with other modules, it appears to be a minimum confidence threshold used in the vivarium/scout package. Its primary purpose is to filter results based on a certain level of confidence. It is likely used in conjunction with the `git_analyzer` module to analyze Git data and the `audit` module to perform audits.
---

# _check_tldr_coverage

**Function Summary: `_check_tldr_coverage`**

Checks all Python files in a repository for corresponding `.tldr.md` files, unless ignored. It returns a boolean indicating success and a list of errors encountered. This function depends on `vivarium/scout/audit.py`, `vivarium/scout/git_analyzer.py`, and `vivarium/scout/ignore.py` for pattern matching and Git analysis.
---

# _check_draft_confidence

**Function Summary: `_check_draft_confidence`**

Checks if no draft or navigation events within the last N hours have confidence below a specified minimum threshold.
It iterates through audit logs, filtering events based on confidence and time constraints, and returns a boolean result and a list of violating events.
This function relies on audit logs and may interact with `vivarium/scout/audit.py`, `vivarium/scout/git_analyzer.py`, and `vivarium/scout/ignore.py` for data and configuration.
---

# _check_hourly_spend

**Function Summary: _check_hourly_spend**

The `_check_hourly_spend` function checks if the hourly spend exceeds a specified limit. It returns a boolean indicating whether the spend is within the limit and a list of error messages if any. This function depends on the `vivarium/scout/audit.py` module for audit log data and may interact with `vivarium/scout/git_analyzer.py` and `vivarium/scout/ignore.py` for additional analysis or filtering.
---

# _check_draft_events_recent

**Function Summary: `_check_draft_events_recent`**

Checks if an audit log has commit_draft events within the last N hours, indicating draft system health. It returns a boolean indicating the presence of such events and a list of related commit hashes. This function depends on the `vivarium/scout/audit.py`, `vivarium/scout/git_analyzer.py`, and `vivarium/scout/ignore.py` modules.
---

# run_ci_guard

**run_ci_guard Function Summary**
=====================================

The `run_ci_guard` function runs all Continuous Integration (CI) checks to ensure the integrity of the draft system. It checks for commit draft events within a specified time frame and returns a boolean indicating whether all checks passed and a list of error messages.

**Key Responsibilities:**

* Run CI checks
* Check for commit draft events within a specified time frame
* Return a boolean indicating whether all checks passed and a list of error messages

**Relationship with Dependencies:**

* Depends on `vivarium/scout/audit.py` for audit functionality
* Depends on `vivarium/scout/git_analyzer.py` for Git analysis
* Depends on `vivarium/scout/ignore.py` for ignoring certain events or files
---

# main

**Summary**

The `main` function serves as the CLI entry point, responsible for executing the program's primary logic. It appears to conditionally call or loop through various functions, returning an integer value. The function interacts with dependencies from `vivarium/scout/*` modules, specifically utilizing functionality from `git_analyzer.py` and `ignore.py`.