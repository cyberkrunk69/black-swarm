# _last_doc_sync_time

## Logic Overview
### Code Flow and Main Steps

The `_last_doc_sync_time` function iterates over a list of Python files (`py_files`) and returns a list of tuples containing the file path and its last modified time (`mtime`). If a `.py` file does not have a corresponding `.docs/*.tldr.md` or `.docs/*.deep.md` file, the `mtime` value is `None`.

Here's a step-by-step breakdown of the code flow:

1. Initialize an empty list `result` to store the file paths and their last modified times.
2. Iterate over each `.py` file in `py_files`.
3. For each `.py` file, construct the path to its `.docs` directory.
4. Iterate over the possible file suffixes (`".tldr.md"` and `".deep.md"`).
5. For each suffix, construct the path to the corresponding documentation file.
6. Check if the documentation file exists. If it does:
   1. Get the last modified time of the documentation file using `stat().st_mtime`.
   2. If this is the first documentation file found for the `.py` file, or if its last modified time is newer than the previously found time, update the `latest` variable with the new time.
7. Append a tuple containing the `.py` file path and its last modified time (or `None` if no documentation file was found) to the `result` list.
8. Return the `result` list.

## Dependency Interactions
### How the Code Uses the Listed Dependencies

The `_last_doc_sync_time` function does not directly use the listed dependencies (`vivarium/scout/audit.py`, `vivarium/scout/git_analyzer.py`, `vivarium/scout/ignore.py`). However, it does use the `Path` class from the `pathlib` module, which is likely imported from one of these dependencies.

The function relies on the `Path` class to manipulate file paths and directories. Specifically, it uses the following methods:

* `parent`: to get the parent directory of a file
* `/`: to join paths
* `exists()`: to check if a file exists
* `stat()`: to get file metadata (last modified time, etc.)

## Potential Considerations
### Edge Cases, Error Handling, and Performance Notes

1. **Error Handling**: The function catches `OSError` exceptions when trying to get the last modified time of a file. However, it does not handle other potential exceptions, such as `PermissionError` or `FileNotFoundError`. Consider adding more robust error handling to handle these cases.
2. **Performance**: The function iterates over each `.py` file and its corresponding documentation files. If the list of `.py` files is large, this could lead to performance issues. Consider using a more efficient data structure or algorithm to improve performance.
3. **File Existence**: The function checks if a documentation file exists before trying to get its last modified time. However, it does not check if the file is a directory or if it has the correct permissions. Consider adding additional checks to handle these cases.
4. **mtime=None**: The function returns `mtime=None` if no documentation file is found for a `.py` file. Consider returning a more informative value, such as a default last modified time or an error message.

## Signature
### Function Signature

```python
def _last_doc_sync_time(repo_root: Path, py_files: List[Path]) -> List[tuple[Path, Optional[float]]]:
    """Return (file, mtime) for each .py file's .docs/*.tldr.md or .deep.md. mtime=None if missing."""
```
---

# _missing_drafts

## Logic Overview
The `_missing_drafts` function is designed to identify staged `.py` files that do not have corresponding draft commit files in the `docs/drafts` directory. Here's a step-by-step breakdown of the code's flow:

1. **Initialization**: The function takes two parameters: `repo_root` (a `Path` object representing the repository root) and `staged_py` (a list of `Path` objects representing staged `.py` files).
2. **Draft Directory Construction**: The function constructs the path to the `docs/drafts` directory by joining the `repo_root` with the `docs` and `drafts` directories.
3. **Iteration**: The function iterates over the `staged_py` list, examining each file.
4. **Stem Extraction**: For each file, the function extracts the stem (the file name without the extension) using the `stem` attribute.
5. **Draft File Path Construction**: The function constructs the path to the corresponding draft commit file by joining the `draft_dir` with the stem and `.commit.txt` extension.
6. **Existence Check**: The function checks if the draft commit file exists using the `exists()` method.
7. **Missing Draft Identification**: If the draft commit file does not exist, the function adds the original `.py` file to the `missing` list.
8. **Return**: The function returns the `missing` list, containing the staged `.py` files that do not have corresponding draft commit files.

## Dependency Interactions
The `_missing_drafts` function does not directly interact with the listed dependencies (`vivarium/scout/audit.py`, `vivarium/scout/git_analyzer.py`, and `vivarium/scout/ignore.py`). However, it is likely that these dependencies are used elsewhere in the codebase, and the `_missing_drafts` function is designed to work in conjunction with these dependencies.

## Potential Considerations
Here are some potential considerations for the `_missing_drafts` function:

* **Edge Cases**: What if the `repo_root` or `staged_py` parameters are `None` or empty? The function should handle these cases to prevent errors.
* **Error Handling**: What if the `draft_dir` or draft commit file does not exist? The function should handle these cases to prevent errors.
* **Performance**: The function iterates over the `staged_py` list, which may be large. Consider using a more efficient data structure or algorithm to improve performance.
* **Path Handling**: The function uses the `Path` object to handle file paths. Consider using the `pathlib` module's `resolve()` method to ensure that paths are resolved correctly.

## Signature
```python
def _missing_drafts(repo_root: Path, staged_py: List[Path]) -> List[Path]:
    """Return staged .py files that don't have docs/drafts/{stem}.commit.txt."""
```
---

# _git_hook_status

## Logic Overview
### Code Flow and Main Steps

The `_git_hook_status` function is designed to check the existence of two specific Git hooks: `prepare-commit-msg` and `post-commit`. Here's a step-by-step breakdown of the code's flow:

1. **Define the function signature**: The function takes a `repo_root` parameter of type `Path` and returns a dictionary with string keys and boolean values.
2. **Construct the hooks directory path**: The function creates a `hooks_dir` path by joining the `repo_root` with the `.git` directory and the `hooks` subdirectory.
3. **Check the existence of hooks**: The function uses the `exists()` method to check if the `prepare-commit-msg` and `post-commit` hooks exist at their respective locations within the `hooks_dir`.
4. **Return a dictionary with hook status**: The function returns a dictionary with two key-value pairs, where the keys are the hook names and the values are boolean indicators of their existence.

## Dependency Interactions
### How the Code Uses Listed Dependencies

The `_git_hook_status` function does not directly use the listed dependencies (`vivarium/scout/audit.py`, `vivarium/scout/git_analyzer.py`, and `vivarium/scout/ignore.py`). However, it does rely on the `Path` type from the `pathlib` module, which is not explicitly listed as a dependency.

## Potential Considerations
### Edge Cases, Error Handling, and Performance Notes

1. **Error handling**: The function does not handle potential errors that may occur when constructing the `hooks_dir` path or checking the existence of hooks. Consider adding try-except blocks to handle these scenarios.
2. **Performance**: The function uses the `exists()` method to check the existence of hooks, which may incur a performance overhead if the repository is large. Consider using a more efficient approach, such as checking the directory contents or using a Git API.
3. **Repository structure**: The function assumes a specific repository structure, where the `.git` directory is located at the root of the repository. Consider adding checks to handle variations in repository structure.
4. **Hook naming conventions**: The function assumes that the hook files follow the standard naming conventions (`prepare-commit-msg` and `post-commit`). Consider adding checks to handle variations in hook naming conventions.

## Signature
### Function Signature

```python
def _git_hook_status(repo_root: Path) -> dict[str, bool]:
    """Check if prepare-commit-msg and post-commit hooks are installed."""
```

The function signature indicates that the function takes a `repo_root` parameter of type `Path` and returns a dictionary with string keys and boolean values. The docstring provides a brief description of the function's purpose.
---

# run_status

## Logic Overview
The `run_status` function generates a status output in a style similar to Git status. It takes a `repo_root` path as input and returns a string containing the status information. The function can be broken down into the following main steps:

1. **Initialization**: The function initializes an empty list `lines` to store the status output lines.
2. **Staged files**: It retrieves the staged files using the `get_changed_files` function and filters out Python files (`*.py`) that are not ignored using the `IgnorePatterns` class.
3. **Last doc-sync**: It checks the last doc-sync status for the staged Python files and appends the result to the `lines` list.
4. **Missing drafts**: It checks for missing commit drafts in the `docs/drafts` directory and appends the result to the `lines` list.
5. **Audit**: It retrieves the hourly spend and accuracy metrics from the `AuditLog` class and appends the result to the `lines` list.
6. **Git hooks**: It checks the status of Git hooks and appends the result to the `lines` list.
7. **Return**: The function returns the concatenated `lines` list as a string.

## Dependency Interactions
The `run_status` function interacts with the following dependencies:

1. **vivarium/scout/audit.py**: The `AuditLog` class is used to retrieve hourly spend and accuracy metrics.
2. **vivarium/scout/git_analyzer.py**: The `_git_hook_status` function is used to check the status of Git hooks.
3. **vivarium/scout/ignore.py**: The `IgnorePatterns` class is used to filter out ignored files.

The function uses the following functions and classes from these dependencies:

* `AuditLog`: `hourly_spend`, `accuracy_metrics`, `close`
* `_git_hook_status`: returns a dictionary of Git hook status
* `IgnorePatterns`: `matches` method to filter out ignored files

## Potential Considerations
The following edge cases, error handling, and performance notes are worth considering:

1. **Error handling**: The function does not handle errors that may occur when interacting with the dependencies. It would be beneficial to add try-except blocks to handle potential errors.
2. **Performance**: The function retrieves the staged files, filters out Python files, and checks the last doc-sync status for each staged file. This may be performance-intensive for large repositories. Consider optimizing this step or using a more efficient approach.
3. **Git hooks**: The function checks the status of Git hooks, but it does not provide any information about the hooks themselves. Consider adding more details about the hooks, such as their names and installation status.
4. **Accuracy metrics**: The function retrieves accuracy metrics from the `AuditLog` class, but it does not provide any information about the metrics themselves. Consider adding more details about the metrics, such as their calculation method and units.

## Signature
```python
def run_status(repo_root: Path) -> str:
    """Generate status output (git status style)."""
```
The function takes a `repo_root` path as input and returns a string containing the status information. The `repo_root` path is expected to be a `Path` object, and the function returns a string.
---

# main

## Logic Overview
### Code Flow and Main Steps

The `main` function serves as the entry point for a command-line interface (CLI) application. Here's a step-by-step breakdown of its execution flow:

1. **Get the Current Working Directory**: The function starts by getting the current working directory using `Path.cwd().resolve()`. This returns the absolute path of the current working directory, which is stored in the `repo_root` variable.
2. **Run the Status Function**: The `repo_root` path is then passed to the `run_status` function, which is imported from an external module (not shown in the provided code snippet). The result of this function call is stored in the `output` variable.
3. **Print the Output**: The `output` variable is then printed to the console using the `print` function.
4. **Return a Status Code**: Finally, the function returns an integer value of 0, indicating successful execution.

### Main Steps Summary

The `main` function consists of four main steps:

* Get the current working directory
* Run the `run_status` function
* Print the output
* Return a status code

## Dependency Interactions
### Imported Modules and Functions

The `main` function interacts with the following external modules and functions:

* `Path`: A class from the `pathlib` module, used to work with file paths.
* `run_status`: A function imported from an external module (not shown in the provided code snippet), used to analyze the repository status.

### Imported Modules

The `main` function imports the following modules:

* `vivarium/scout/audit.py`: Not used in the provided code snippet.
* `vivarium/scout/git_analyzer.py`: Not used in the provided code snippet.
* `vivarium/scout/ignore.py`: Not used in the provided code snippet.

### Imported Functions

The `main` function imports the following functions:

* `run_status`: A function imported from an external module (not shown in the provided code snippet), used to analyze the repository status.

## Potential Considerations
### Edge Cases and Error Handling

The `main` function does not handle any potential edge cases or errors that may occur during its execution. This includes:

* **Repository not found**: If the repository is not found at the specified path, the `run_status` function may raise an exception.
* **Invalid repository status**: If the `run_status` function returns an invalid or unexpected status, the `main` function may not handle it correctly.

### Performance Notes

The `main` function does not have any significant performance implications. However, the `run_status` function may have performance implications depending on the complexity of the repository analysis.

## Signature
### Function Signature

The `main` function has the following signature:

```python
def main() -> int:
    """CLI entry point."""
```

This indicates that the function takes no arguments and returns an integer value. The docstring provides a brief description of the function's purpose.