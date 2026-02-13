# _handle_generate

Handles the 'generate' subcommand by resolving the target path, validating its existence, and either running a dry-run preview or invoking doc generation for a file or directory. It relies on `vivarium/scout/audit.py`, `vivarium/scout/doc_generation.py`, and `vivarium/scout/tools.py` for functionality.
---

# _print_dry_run

**_print_dry_run Function Summary**
=====================================

The `_print_dry_run` function prints what actions would be taken without executing them. It takes a target path, an optional output directory, and a recursive flag as input, and handles exceptions accordingly. This function appears to be part of a larger workflow involving doc generation and audit tools from the vivarium/scout package.
---

# _handle_update

Handles the 'update' subcommand, likely responsible for updating documentation or other resources. It returns an integer value, possibly indicating the outcome of the update operation. The function interacts with dependencies from vivarium/scout, specifically audit, doc_generation, and tools modules.
---

# _handle_status

Handles the 'status' subcommand, likely displaying or updating the status of a project or process. It returns an integer value indicating success or failure. The function interacts with modules from vivarium/scout, utilizing tools and doc generation for status updates.
---

# main

**Main Function Summary**
==========================

The `main` function serves as the entry point, setting up parsers, parsing arguments, and dispatching to the appropriate handler based on the subcommand. It returns an integer value. The function interacts with `vivarium/scout/audit.py`, `vivarium/scout/doc_generation.py`, and `vivarium/scout/tools.py` to perform its tasks.