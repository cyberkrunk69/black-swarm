# _DOC_EXTENSIONS

## Logic Overview
The code defines a constant `_DOC_EXTENSIONS` which is a set containing four string values representing file extensions: `.py`, `.js`, `.mjs`, and `.cjs`. This constant is likely used to identify or filter files based on their extensions.

## Dependency Interactions
There are no direct interactions with the traced imports (`vivarium/scout/doc_generation.py`, `vivarium/scout/git_analyzer.py`, `vivarium/scout/git_drafts.py`, `vivarium/scout/cli/status.py`) in the provided code snippet. The constant is defined independently without referencing any of the imported modules.

## Potential Considerations
The code does not include any error handling or conditional logic. It simply defines a constant set of file extensions. Potential considerations may include:
- The set data structure implies that the order of file extensions does not matter, and duplicates are automatically removed (although there are no duplicates in this case).
- The constant is prefixed with an underscore, which is a Python convention indicating that the variable is intended to be private.
- The choice of file extensions may be relevant for a specific use case, such as identifying files that contain code or documentation.

## Signature
N/A
---

# _resolve_pr_files

## Logic Overview
The `_resolve_pr_files` function is designed to resolve which files to include in a PR description based on a set of predefined priorities. The main steps in the function are:
1. Check if explicit files are provided (`args.files`).
2. If not, check if a base branch is specified (`args.base_branch`).
3. If neither of the above is provided, it checks for an upstream reference.
4. If no upstream reference is found, it attempts to find a default base reference (e.g., `origin/main` or `origin/master`).
5. If all else fails, it falls back to using staged files.

## Dependency Interactions
The function interacts with the following traced calls:
- `p.exists`: Checks if a file exists.
- `p.is_absolute`: Checks if a path is absolute.
- `p.resolve`: Resolves a path to its absolute form.
- `pathlib.Path`: Creates a new `Path` object.
- `print`: Prints warning messages to the standard error stream.
- `repo_root.resolve`: Resolves the repository root path.
- `resolved.append`: Adds a resolved file path to the `resolved` list.
- `vivarium.scout.git_analyzer.get_changed_files`: Retrieves a list of changed files based on the provided parameters.
- `vivarium.scout.git_analyzer.get_default_base_ref`: Retrieves the default base reference.
- `vivarium.scout.git_analyzer.get_upstream_ref`: Retrieves the upstream reference.

## Potential Considerations
The function handles the following edge cases and considerations:
- Non-existent files: If a file specified in `args.files` does not exist, it prints a warning message and skips the file.
- Non-absolute paths: If a path in `args.files` is not absolute, it resolves the path relative to the repository root.
- No upstream reference: If no upstream reference is found, it attempts to find a default base reference.
- No default base reference: If no default base reference is found, it falls back to using staged files.
- Performance: The function uses list comprehensions to filter files based on their suffix, which may impact performance for large lists of files.

## Signature
The function signature is:
```python
def _resolve_pr_files(args: argparse.Namespace, repo_root: Path) -> tuple[list[Path], str]
```
This indicates that the function:
- Takes two parameters: `args` of type `argparse.Namespace` and `repo_root` of type `Path`.
- Returns a tuple containing a list of `Path` objects and a string. The list of `Path` objects represents the resolved file paths, and the string represents the mode used to resolve the files (e.g., "explicit file list", "git diff --base-branch", etc.).
---

# _cmd_commit

## Logic Overview
The `_cmd_commit` function handles the scout commit subcommand. It follows these main steps:
1. **Determine the repository root**: It uses `pathlib.Path.cwd().resolve()` to get the current working directory.
2. **Get staged files**: It calls `vivarium.scout.git_analyzer.get_changed_files` with `staged_only=True` to get the list of staged files.
3. **Filter for Python files**: It filters the staged files to only include files with a `.py` suffix.
4. **Handle no staged files**: If there are no staged Python files, it prints an error message and returns 1.
5. **Handle commit without draft**: If `args.use_draft` is False, it runs `git commit` without a draft, which opens an editor for the user to input a commit message.
6. **Assemble commit message**: If `args.use_draft` is True, it calls `vivarium.scout.git_drafts.assemble_commit_message` to assemble a commit message based on the staged Python files.
7. **Preview or commit**: Depending on the value of `args.preview`, it either prints the commit message to stdout or writes it to a temporary file and runs `git commit -F <temp>`.

## Dependency Interactions
The function interacts with the following dependencies:
* `pathlib.Path`: Used to get the current working directory (`pathlib.Path.cwd().resolve()`).
* `pathlib.Path.cwd`: Used to get the current working directory.
* `vivarium.scout.git_analyzer.get_changed_files`: Called to get the list of staged files.
* `vivarium.scout.git_drafts.assemble_commit_message`: Called to assemble a commit message based on the staged Python files.
* `subprocess.run`: Used to run `git commit` commands.
* `tempfile.NamedTemporaryFile`: Used to create a temporary file for the commit message.
* `print`: Used to print error messages or the commit message for preview.
* `f.write`: Used to write the commit message to the temporary file.

## Potential Considerations
The function handles the following edge cases and errors:
* **No staged files**: It prints an error message and returns 1 if there are no staged Python files.
* **Commit without draft**: It runs `git commit` without a draft if `args.use_draft` is False.
* **Error running git commit**: It catches `subprocess.CalledProcessError`, `FileNotFoundError`, and `OSError` exceptions when running `git commit` commands and prints an error message.
* **Temporary file creation**: It uses `tempfile.NamedTemporaryFile` to create a temporary file for the commit message, which is deleted after use.
* **Performance**: The function uses `subprocess.run` to run `git commit` commands, which may have performance implications if the repository is large.

## Signature
The function signature is:
```python
def _cmd_commit(args: argparse.Namespace) -> int
```
It takes an `argparse.Namespace` object as input and returns an integer value. The `argparse.Namespace` object is expected to contain the command-line arguments, including `args.use_draft` and `args.preview`. The return value is 0 on success and 1 on error.
---

# _cmd_pr_auto_draft

## Logic Overview
The `_cmd_pr_auto_draft` function generates a PR description and writes it to a file named `.github/pr-draft.md`. The main steps are:
1. Create the output directory if it does not exist.
2. Build the PR description from drafts or raw summaries.
3. Add a versioned docs link if available.
4. Add an impact section from the call graph if the call graph file exists and there are Python files.
5. Append the stale status.
6. Write the description to the output file.

## Dependency Interactions
The function uses the following traced calls:
- `call_graph_path.exists()`: checks if the call graph file exists.
- `content.splitlines()`: splits the content of the version file into lines.
- `f.relative_to(repo_root)`: gets the relative path of a file to the repository root.
- `len()`: gets the length of a list (e.g., the number of impact modules).
- `line.split()`: splits a line into parts (e.g., to extract the version number).
- `line.startswith()`: checks if a line starts with a certain string (e.g., "version:").
- `out_path.parent.mkdir()`: creates the output directory if it does not exist.
- `out_path.write_text()`: writes the description to the output file.
- `print()`: prints a message to the standard error stream.
- `str()`: converts an object to a string (e.g., a file path).
- `version_file.exists()`: checks if the version file exists.
- `version_file.read_text()`: reads the content of the version file.
- `vivarium.scout.doc_generation.find_stale_files()`: finds stale files in the repository.
- `vivarium.scout.doc_generation.get_downstream_impact()`: gets the downstream impact of the changed files.
- `vivarium.scout.doc_generation.synthesize_pr_description()`: synthesizes the PR description from raw summaries.
- `vivarium.scout.git_drafts.assemble_pr_description()`: assembles the PR description from drafts.

## Potential Considerations
The function handles the following edge cases and errors:
- If the version file does not exist, the function does not add a versioned docs link.
- If the call graph file does not exist or there are no Python files, the function does not add an impact section.
- If there are stale files, the function appends a stale status section to the description.
- If there is an error reading the version file, the function catches the `OSError` exception and continues without adding a versioned docs link.
- If there is an error getting the relative path of a file, the function catches the `ValueError` exception and uses the absolute path instead.

The function also considers performance by:
- Only reading the version file if it exists.
- Only finding stale files if the vivarium directory exists.
- Only getting the downstream impact if the call graph file exists and there are Python files.

## Signature
The function signature is:
```python
def _cmd_pr_auto_draft(repo_root: Path, py_files: list[Path], mode: str) -> int
```
The function takes three parameters:
- `repo_root`: the root directory of the repository (type `Path`).
- `py_files`: a list of Python files (type `list[Path]`).
- `mode`: a string parameter (type `str`).
The function returns an integer value (type `int`). Note that the `mode` parameter is not used in the function.
---

# _find_gh

## Logic Overview
The `_find_gh` function attempts to find the path to the `gh` CLI. The main steps are:
1. Run a subprocess with the command `which gh` to find the path to the `gh` CLI.
2. Capture the output of the subprocess.
3. If the subprocess runs successfully, return the path to the `gh` CLI after stripping any leading or trailing whitespace.
4. If the subprocess fails or the `gh` CLI is not found, return `None`.

## Dependency Interactions
The function interacts with the following dependencies:
- `subprocess.run`: This function is used to run the `which gh` command in a subprocess. The qualified name of this call is `subprocess.run`.
- `result.stdout.strip`: This method is used to remove any leading or trailing whitespace from the output of the subprocess. The qualified name of this call is `str.strip`.

## Potential Considerations
The function handles the following edge cases and errors:
- `subprocess.CalledProcessError`: This exception is raised if the subprocess returns a non-zero exit code, indicating that the `gh` CLI was not found or the `which` command failed.
- `FileNotFoundError`: This exception is raised if the `which` command is not found.
- The function returns `None` if the `gh` CLI is not found or if an error occurs while running the subprocess.
- The function uses the `check=True` argument with `subprocess.run`, which means that if the subprocess returns a non-zero exit code, a `subprocess.CalledProcessError` exception is raised.

## Signature
The function signature is `def _find_gh() -> str | None`, indicating that:
- The function name is `_find_gh`.
- The function takes no arguments.
- The function returns either a string (`str`) representing the path to the `gh` CLI or `None` if the `gh` CLI is not found.
---

# _cmd_pr

## Logic Overview
The `_cmd_pr` function handles the scout pr subcommand. It follows these main steps:
1. Resolves Python files based on the provided arguments and repository root.
2. Checks for the `--auto-draft` flag and calls `_cmd_pr_auto_draft` if set.
3. If no Python files are found, it prints an error message and returns 1.
4. If the `--no-use-draft` flag is set, it skips draft assembly and returns 0.
5. Assembles a PR description using `assemble_pr_description` and synthesizes it using `synthesize_pr_description`.
6. If the `--create` flag is set, it creates a PR using the GitHub CLI.
7. If the `--create` flag is not set, it prints the PR description.

## Dependency Interactions
The `_cmd_pr` function interacts with the following dependencies:
* `_cmd_pr_auto_draft`: called when the `--auto-draft` flag is set.
* `_find_gh`: checks if the GitHub CLI is installed.
* `_resolve_pr_files`: resolves Python files based on the provided arguments and repository root.
* `vivarium.scout.doc_generation.synthesize_pr_description`: synthesizes the PR description.
* `vivarium.scout.git_analyzer.get_current_branch`: gets the current branch.
* `vivarium.scout.git_analyzer.get_default_base_ref`: gets the default base reference.
* `vivarium.scout.git_analyzer.get_upstream_ref`: gets the upstream reference.
* `vivarium.scout.git_analyzer.has_remote_origin`: checks if the repository has a remote origin.
* `vivarium.scout.git_analyzer.is_remote_empty`: checks if the remote repository is empty.
* `vivarium.scout.git_drafts.assemble_pr_description`: assembles the PR description.
* `pathlib.Path`: used to create a temporary file for the PR description.
* `subprocess.run`: used to run GitHub CLI commands.
* `tempfile.NamedTemporaryFile`: used to create a temporary file for the PR description.
* `argparse.Namespace`: used to parse command-line arguments.

## Potential Considerations
The code handles the following edge cases and potential considerations:
* Checks for the existence of Python files before proceeding.
* Handles the case where the repository has no remote origin or is empty.
* Handles the case where the current branch is not set.
* Handles errors when running GitHub CLI commands.
* Uses a temporary file to store the PR description, which is deleted after use.
* Uses the `subprocess.run` function with the `check=True` argument to raise an exception if the command fails.
* Uses the `try-except` block to catch and handle exceptions when running GitHub CLI commands.

## Signature
The `_cmd_pr` function has the following signature:
```python
def _cmd_pr(args: argparse.Namespace) -> int
```
It takes an `argparse.Namespace` object as an argument and returns an integer. The integer return value indicates the exit status of the function, where 0 indicates success and non-zero values indicate errors.
---

# main

## Logic Overview
The `main` function is the entry point for the scout root CLI. It defines an `ArgumentParser` with subparsers for different commands: `commit`, `pr`, and `status`. The function then parses the arguments and executes the corresponding command. The main steps are:
- Define the parser and subparsers
- Parse the arguments
- Execute the corresponding command based on the parsed arguments
- If no command is specified, print the help message and return 0

## Dependency Interactions
The `main` function interacts with the following traced calls:
- `argparse.ArgumentParser`: creates a new argument parser
- `parser.add_subparsers`: adds subparsers to the parser
- `subparsers.add_parser`: adds a new parser for each command (`commit`, `pr`, `status`)
- `commit_parser.add_argument` and `pr_parser.add_argument`: add arguments to the `commit` and `pr` parsers
- `parser.parse_args`: parses the command-line arguments
- `parser.print_help`: prints the help message if no command is specified
- `_cmd_commit` and `_cmd_pr`: calls the corresponding command functions based on the parsed arguments
- `run_status`: calls the `run_status` function from `vivarium.scout.cli.status` for the `status` command
- `pathlib.Path.cwd`: gets the current working directory for the `status` command
- `print`: prints the result of the `run_status` function for the `status` command

## Potential Considerations
The code does not explicitly handle errors, but it does return an integer value, which could be used to indicate success or failure. The `argparse` library will raise an exception if there are any errors parsing the arguments. The code also does not handle any potential exceptions that may be raised by the `_cmd_commit`, `_cmd_pr`, or `run_status` functions. Additionally, the performance of the code may be affected by the complexity of the argument parsing and the execution of the corresponding commands.

## Signature
The `main` function is defined as `def main() -> int`, indicating that it takes no arguments and returns an integer value. The return value is used to indicate the success or failure of the command execution. The function does not take any arguments, which is typical for a command-line interface entry point.