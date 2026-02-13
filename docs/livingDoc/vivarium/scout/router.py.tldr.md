# logger

**Logger Constant Summary**
==========================

The `logger` constant is not explicitly documented, but it appears to be a logging utility used throughout the vivarium/scout project. Its primary purpose is to handle logging operations, such as logging messages, errors, and other events. It likely interacts with various dependencies, including `vivarium/scout/audit.py` and `vivarium/scout/llm.py`, to log relevant information.
---

# TOKENS_PER_SMALL_FILE

**TOKENS_PER_SMALL_FILE**
==========================

The `TOKENS_PER_SMALL_FILE` constant is not explicitly documented, but based on its interactions with other modules, it appears to be a threshold value used to determine the size of small files in a Git repository. Its primary purpose is to help identify and analyze small files, possibly for code quality or security audits. It is likely used in conjunction with the `vivarium/scout/audit.py` module to analyze and report on file sizes.
---

# COST_PER_MILLION_8B

The Python constant 'COST_PER_MILLION_8B' is not explicitly documented, but based on its name, it appears to represent a cost associated with 1 million units of 8 billion. 

Its primary purpose is to store a monetary value. 

It does not have a direct relationship with the listed dependencies, but it may be used in calculations or comparisons within the vivarium/scout module.
---

# COST_PER_MILLION_70B

The Python constant 'COST_PER_MILLION_70B' is not explicitly documented, but based on its name, it appears to represent a cost per million units of a 70 billion entity, likely a financial metric. Its primary purpose is to store a monetary value. It likely interacts with the vivarium/scout/llm.py module, which handles large language models, possibly for financial analysis or forecasting.
---

# BRIEF_COST_PER_FILE

The Python constant 'BRIEF_COST_PER_FILE' is not explicitly documented, but based on its interactions with various modules, it appears to represent a cost value associated with file operations. Its primary purpose is to provide a cost metric for file-related activities, and it is likely used in conjunction with the vivarium/scout/validator.py module to validate file costs.
---

# TASK_NAV_ESTIMATED_COST

The Python constant 'TASK_NAV_ESTIMATED_COST' is not explicitly documented, but based on its name, it likely represents the estimated cost of navigation in a task or environment. Its primary purpose is to provide a numerical value for cost estimation. It may be used in conjunction with the vivarium/scout/llm.py module for language model-based tasks.
---

# DRAFT_COST_PER_FILE

The Python constant 'DRAFT_COST_PER_FILE' is not explicitly documented, but based on its interactions with other modules, it appears to represent a cost value associated with a file in a draft context. Its primary purpose is to provide a monetary value for draft file costs, likely used in calculations or validation processes. It is likely used in conjunction with the `vivarium/scout/validator.py` module for draft validation and cost estimation.
---

# NavResult

**NavResult Class Summary**
==========================

The `NavResult` class represents the result of a scout-nav LLM (Large Language Model) call. Its primary purpose is to encapsulate the outcome of this call, which likely involves analyzing and validating code or other data. The class interacts with various dependencies, including LLM-related modules, to facilitate this analysis and validation process.
---

# SymbolDoc

**SymbolDoc Class Summary**

The `SymbolDoc` class generates symbol documentation. Its primary purpose is to create documentation for symbols based on the provided information. It relies on various dependencies, including vivarium/scout modules, to gather and process data for generating accurate documentation.
---

# _notify_user

**Notify User Function Summary**
================================

The `_notify_user` function is a stub that notifies the user of a message. Its primary purpose is to display a message to the user, and it is intended to be overridden for testing or real UI implementation.

It has no explicit logic, but is expected to call other functions or modules to perform the actual notification. The function's relationship with its dependencies is unclear, but it likely interacts with them to display the message to the user.
---

# TriggerRouter

**TriggerRouter Class Summary**
================================

The `TriggerRouter` class orchestrates triggers, respecting limits and preventing infinite loops, while safely cascading doc updates. It is responsible for managing trigger interactions and ensuring efficient doc update propagation. The class interacts with various dependencies, including validation, configuration, and Git analysis modules, to facilitate trigger management and doc updates.
---

# __init__

**__init__ Method Summary**

The `__init__` method initializes an object, setting its attributes based on provided configuration, audit log, validator, repository root, and notification function. It calls other methods to perform tasks such as analyzing the Git repository and validating the configuration. The method interacts with various dependencies, including ScoutConfig, AuditLog, Validator, and GitAnalyzer, to perform its tasks.
---

# should_trigger

**should_trigger Method Summary**
================================

The `should_trigger` method filters out ignored files from a given list and returns a relevant subset. It is responsible for determining which files should be processed based on the provided configuration and ignore rules. The method interacts with various dependencies, including configuration and ignore rules, to make this determination.
---

# _quick_token_estimate

**Quick Symbol/Code Size Estimate Method**
=============================================

The `_quick_token_estimate` method provides a quick estimate of symbol or code size for cost prediction. It takes a file path as input and returns an integer estimate. The method likely handles exceptions, makes conditional checks, and calls other functions to gather information from dependencies such as Git analyzers and LLM (Large Language Model) modules.
---

# estimate_cascade_cost

**estimate_cascade_cost Method Summary**
=====================================

The `estimate_cascade_cost` method predicts the cost of a cascade before any Large Language Model (LLM) calls, aiming for a conservative estimate to stay under budget. It takes a list of file paths as input and returns a float representing the estimated cost. This method likely interacts with various dependencies to gather information about the files, such as their size, complexity, and potential LLM usage.
---

# on_file_save

**on_file_save Method Summary**

The `on_file_save` method is called when a file is saved, likely by an IDE integration or file watcher. It is responsible for validating and processing the saved file, potentially involving conditional checks, loops, and calls to other modules. The method interacts with various dependencies, including validators, config, and Git analyzers, to ensure the file is properly processed and updated.
---

# on_git_commit

**on_git_commit Method Summary**

The `on_git_commit` method is called by a git hook or CI, responsible for analyzing changes made to the repository. It iterates over changed files, potentially calling other methods to validate and process the changes, and returns without a value. The method interacts with various dependencies to perform its tasks, including file validators, git analyzers, and configuration readers.
---

# prepare_commit_msg

**Summary**

The `prepare_commit_msg` method prepares a commit message by generating a draft for staged `.py` files. It assembles the commit message by processing each staged file and writing it to a specified file. This method does not block the commit process on failure and uses a global semaphore for exception handling.
---

# estimate_task_nav_cost

**estimate_task_nav_cost Method Summary**
=====================================

The `estimate_task_nav_cost` method estimates the cost for task-based navigation, considering a base cost of 8 bytes, potential retry costs, and possible additional costs of 70 bytes. It returns a float representing the estimated cost. This method likely interacts with various dependencies to gather information necessary for the cost estimation.
---

# _list_python_files

**_list_python_files Method Summary**
=====================================

The `_list_python_files` method lists Python files for context, optionally scoped to a specified directory. It iterates through the directory tree, filtering out ignored files and returning a limited list of Python files.

**Key Responsibilities:**

* Iterate through directory tree
* Filter out ignored files
* Return a limited list of Python files

**Relationship with Dependencies:**

* Uses `vivarium/scout/ignore.py` to filter out ignored files
* May interact with `vivarium/scout/validator.py` and `vivarium/scout/git_analyzer.py` for additional context.
---

# _parse_nav_json

The `_parse_nav_json` method extracts JSON data from a Large Language Model (LLM) response, potentially wrapped in markdown. It is responsible for parsing the content and returning the extracted JSON data as a dictionary. The method likely interacts with the `vivarium/scout/llm.py` module to handle the LLM response.
---

# navigate_task

**navigate_task Method Summary**
================================

The `navigate_task` method is an asynchronous entry point for CLI task navigation, responsible for executing a task based on a given task string. It attempts to execute the task using `scout-index` (free) and then falls back to a Large Language Model (LLM) if necessary.

It interacts with various dependencies to validate, analyze, and execute the task, including `scout-index`, LLM, and other scout modules for configuration, validation, and exception handling.
---

# on_manual_trigger

**on_manual_trigger Method Summary**
=====================================

The `on_manual_trigger` method is called by CLI commands `scout-nav` and `scout-brief`. It processes a list of files and performs a task based on the provided input, utilizing various dependencies for validation, analysis, and configuration. The method iterates over the files, applies conditional logic, and calls other functions to execute the task.
---

# _quick_parse

**_quick_parse Method Summary**

The `_quick_parse` method is a quick parsing function that extracts signatures and exports from a given file. It handles exceptions, conditional checks, and returns a string result. This method depends on various scout modules for configuration, validation, and Git analysis, and is likely used in the context of code auditing or analysis.
---

# _scout_nav

**_scout_nav Method Summary**
================================

The `_scout_nav` method generates navigation suggestions based on a file, context, and model. It is responsible for exception handling, returning results, and making calls to other dependencies. It interacts with various scout modules to gather information and provide navigation suggestions.
---

# _affects_module_boundary

The `_affects_module_boundary` method determines if a change affects the interface of a module. It checks if the change impacts the module's public API, returning a boolean result. This method likely interacts with the `vivarium/scout/validator.py` to validate the change and `vivarium/scout/git_analyzer.py` to analyze the Git history for changes.
---

# _is_public_api

**Summary**

The `_is_public_api` method determines whether a file is part of the public API based on its directory location. It returns a boolean indicating whether the file is public or not. The method relies on the file's directory being in the public API directory, as indicated by the `vivarium/scout/config.py` configuration.
---

# _detect_module

**_detect_module Method Summary**
=====================================

The `_detect_module` method detects the module name from a given file path. It is responsible for handling exceptions, making conditional checks, and returning the detected module name. The method interacts with various dependencies, including configuration and validation modules, to determine the module name.
---

# _critical_path_files

The `_critical_path_files` method returns a set of files considered critical, which triggers a PR draft. It is responsible for identifying and selecting these critical files based on the project's configuration and validation rules. The method interacts with various dependencies, including configuration and validation modules, to determine the critical files.
---

# _generate_symbol_doc

**_generate_symbol_doc Method Summary**
=====================================

The `_generate_symbol_doc` method generates a symbol doc (stub) based on the provided file, navigation result, and validation result. It is responsible for creating a symbol doc object, which is likely used for documentation or analysis purposes. The method interacts with various dependencies, including validation, configuration, and Git analysis modules, to gather necessary information for generating the symbol doc.
---

# _write_draft

The `_write_draft` method writes a draft to the `docs/drafts/` directory. It takes a file path and a `SymbolDoc` object as input, and returns the file path. This method is responsible for handling exceptions and calling other functions to perform the draft writing process. It interacts with various dependencies to validate and analyze the draft.
---

# _update_module_brief

**_update_module_brief Method Summary**

The `_update_module_brief` method updates the documentation for a specific module by writing to a file in the `docs/drafts/modules` directory. It takes a module name, a trigger file, and a session ID as input, and returns a float value. This method interacts with various dependencies to validate and analyze the module's changes.
---

# _create_human_ticket

**_create_human_ticket Method Summary**
=====================================

The `_create_human_ticket` method creates a human escalation ticket based on provided file, navigation result, and validation result. It handles exceptions and calls other methods to perform the necessary tasks. This method interacts with various dependencies, including validation, navigation, and Git analysis, to gather information for the ticket creation.
---

# _create_pr_draft

**Summary**

The `_create_pr_draft` method creates a pull request draft for the critical path of a project. It is responsible for preparing the necessary information and interacting with various dependencies to generate the draft. This method relies on several Scout dependencies, including `git_analyzer`, `git_drafts`, and `llm`, to analyze the project's code and generate the draft.
---

# _load_symbol_docs

**Summary**

The `_load_symbol_docs` method loads existing symbol documentation from a specified file path, handling exceptions and returning the loaded documentation as a string. It appears to be responsible for reading and processing documentation files in the `.docs/` or `docs/livingDoc/` directories. This method likely interacts with various dependencies to validate and analyze the loaded documentation.
---

# _generate_commit_draft

**Summary**

The `_generate_commit_draft` method generates a conventional commit message draft for staged changes. It is responsible for analyzing the staged changes, determining the type of commit, and creating a draft message. This method interacts with various dependencies to gather information about the staged changes, such as file paths, commit types, and ignore rules.
---

# _generate_pr_snippet

**_generate_pr_snippet Method Summary**
=====================================

The `_generate_pr_snippet` method generates a PR description snippet for a changed file based on the provided file path and session ID. It is responsible for conditional checks, exception handling, and calling other methods to gather necessary information. The method relies on various dependencies, including `vivarium/scout/audit.py` for file analysis and `vivarium/scout/llm.py` for language model interactions.
---

# _generate_impact_summary

**_generate_impact_summary Method Summary**
=============================================

The `_generate_impact_summary` method generates an impact analysis summary for a changed file. It is responsible for analyzing the file's changes and summarizing the impact. The method depends on various scout modules for configuration, validation, and analysis, and uses the Git analyzer to gather information about the file's history.
---

# _process_file

**Summary**

The `_process_file` method processes a single file by navigating through a series of steps: validation, brief analysis, and cascading operations. It takes a file path and a session ID as input, and its primary responsibilities include conditional checks, function calls, and exception handling. The method interacts with various dependencies, including validators, Git analyzers, and LLM (Large Language Model) components, to perform its tasks.