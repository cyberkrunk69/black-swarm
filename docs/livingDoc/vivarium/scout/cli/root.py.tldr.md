# _cmd_commit

**Function Summary: `_cmd_commit`**

The `_cmd_commit` function handles the scout commit subcommand by aggregating commit messages from draft files and committing changes to Git. It filters for `.py` files, reads draft commit messages, and writes the aggregated message to a temporary file or prints it to stdout based on the `--preview` flag. It interacts with `git_analyzer`, `git_drafts`, and `status` modules to perform its tasks.
---

# _cmd_pr

Handles the scout PR subcommand by aggregating draft PR descriptions from `.py` files and printing the result to stdout. It depends on `git_analyzer`, `git_drafts`, and `status` modules to retrieve and process draft files.
---

# main

**Main Function Summary**
==========================

The `main` function serves as the entry point for the scout root CLI, responsible for executing the primary logic of the application. It appears to conditionally execute tasks, returning an integer value upon completion. The function interacts with `git_analyzer.py`, `git_drafts.py`, and `status.py` to perform its tasks.