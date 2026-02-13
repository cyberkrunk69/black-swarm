# logger

The Python constant 'logger' is not a standard constant. However, it is commonly used as a variable name for a logger object in Python's built-in logging module. Its primary purpose is to handle logging operations, such as logging messages at different levels (e.g., debug, info, warning, error, critical).
---

# _run_git

**_run_git Function Summary**
==========================

The `_run_git` function runs a git command, logs the command, and raises an exception on failure. It takes a list of arguments and an optional current working directory as input, and returns the result of the git command execution. It raises a `FileNotFoundError` if the git executable is not found, and a `subprocess.CalledProcessError` if the git command returns a non-zero exit code.
---

# get_changed_files

**get_changed_files Function Summary**
=====================================

The `get_changed_files` function returns a list of changed file paths based on the Git repository changes. It takes into account staged files, working directory changes, and changes relative to a base branch. The function interacts with the Git repository and returns a list of `pathlib.Path` objects representing the changed files.
---

# get_diff_for_file

**get_diff_for_file Function Summary**
=====================================

The `get_diff_for_file` function returns the raw diff string for a specified file. It takes a file path, an optional `staged_only` flag, and an optional `repo_root` directory as input. The function interacts with the Git command to generate the diff string.
---

# get_current_branch

**get_current_branch Function Summary**
=====================================

The `get_current_branch` function retrieves the name of the current branch in a Git repository. It takes an optional `repo_root` parameter, which defaults to the current working directory, and returns the branch name or an empty string if the HEAD is detached or an error occurs.
---

# get_base_branch

**get_base_branch Function Summary**
=====================================

The `get_base_branch` function determines the base branch for the current branch by attempting to find a remote tracking branch, then checking for specific branch names ('main', 'master', 'develop'). It returns the base branch name or `None` if ambiguous or unavailable.