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
The `_cmd_pr_auto_draft` function generates a PR description and writes it to a file named `pr-draft.md` in the `.github` directory of the repository root. The main steps are:
1. Create the output directory if it does not exist.
2. Build the PR description from drafts or raw summaries of changed files.
3. Add a versioned docs link if a `VERSION` file exists in the `docs/livingDoc` directory.
4. Add an impact section from the call graph if a `call_graph.json` file exists and there are changed Python files.
5. Append a stale status section if the `vivarium` directory exists.
6. Write the PR description to the output file and print a success message.

## Dependency Interactions
The function uses the following traced calls:
* `call_graph_path.exists()`: checks if the `call_graph.json` file exists.
* `content.splitlines()`: splits the content of the `VERSION` file into lines.
* `f.relative_to(repo_root)`: gets the relative path of a file to the repository root.
* `getattr(args, "fallback_template", False)`: gets the `fallback_template` attribute from the `args` object, defaulting to `False` if it does not exist.
* `len()`: gets the length of a list, such as the number of changed files or stale files.
* `line.split()`: splits a line into parts, such as to extract the version number from the `VERSION` file.
* `line.startswith()`: checks if a line starts with a certain string, such as "version:".
* `out_path.parent.mkdir()`: creates the output directory if it does not exist.
* `out_path.write_text()`: writes the PR description to the output file.
* `print()`: prints a success message.
* `str()`: converts an object to a string, such as to convert a file path to a string.
* `version_file.exists()`: checks if the `VERSION` file exists.
* `version_file.read_text()`: reads the content of the `VERSION` file.
* `vivarium.scout.doc_generation.find_stale_files()`: finds stale files in the `vivarium` directory.
* `vivarium.scout.doc_generation.get_downstream_impact()`: gets the downstream impact of changed files from the call graph.
* `vivarium.scout.doc_generation.synthesize_pr_description()`: synthesizes the PR description from raw summaries.
* `vivarium.scout.git_drafts.assemble_pr_description()`: assembles the PR description from drafts.

## Potential Considerations
The function handles the following edge cases and errors:
* If the `VERSION` file does not exist, the function does not add a versioned docs link.
* If the `call_graph.json` file does not exist or there are no changed Python files, the function does not add an impact section.
* If the `vivarium` directory does not exist, the function does not append a stale status section.
* If there are more than 10 stale files, the function only lists the first 10 and indicates that there are more.
* The function catches `OSError` exceptions when reading the `VERSION` file and ignores them.
* The function catches `ValueError` exceptions when getting the relative path of a file and uses the absolute path instead.

## Signature
The function signature is:
```python
def _cmd_pr_auto_draft(repo_root: Path, py_files: list[Path], mode: str, args: argparse.Namespace) -> int
```
The function takes four parameters:
* `repo_root`: the path to the repository root.
* `py_files`: a list of paths to changed Python files.
* `mode`: a string indicating the mode of operation (not used in the function).
* `args`: an `argparse.Namespace` object containing additional arguments (only used to get the `fallback_template` attribute).
The function returns an integer indicating the result of the operation (always 0 in this implementation).
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
The `_cmd_pr` function handles the `scout pr` subcommand. It follows a specific order for file resolution:
1. `--from-docs PATH`: Ignores Git and reads `.tldr.md` under `PATH/.docs/`.
2. `--files` or `-f`: Uses an explicit file list, bypassing Git diff.
3. `--base-branch`: Uses `git diff --name-only base...HEAD`.
4. `upstream`: Uses `git diff --name-only @{upstream}..HEAD` if on a branch with an upstream.
5. Default: Uses staged files.

The function then aggregates PR descriptions from `docs/drafts/{stem}.pr.md` per file and handles the following actions:
- Prints to stdout if `--preview`.
- Runs `gh pr create` if `--create`.
- Writes to `.github/pr-draft.md` if `--auto-draft`.

## Dependency Interactions
The function interacts with the following traced calls:
- `_cmd_pr_auto_draft`: Called when `--auto-draft` is used.
- `_find_gh`: Checks if the GitHub CLI is installed.
- `_resolve_pr_files`: Resolves PR files based on the provided arguments.
- `branch.replace`: Replaces characters in the branch name to create a title.
- `f.write`: Writes the PR description to a temporary file.
- `getattr`: Retrieves the `fallback_template` attribute from the `args` object.
- `gh_args.extend`: Adds arguments to the `gh` command.
- `out_path.parent.mkdir`: Creates the parent directory for the output file.
- `out_path.write_text`: Writes the PR description to the output file.
- `pathlib.Path`: Creates a Path object for the repository root.
- `pathlib.Path.cwd`: Gets the current working directory.
- `print`: Prints messages to the console.
- `str`: Converts objects to strings.
- `subprocess.run`: Runs external commands, such as `git` and `gh`.
- `tempfile.NamedTemporaryFile`: Creates a temporary file for the PR description.
- `vivarium.scout.doc_generation.synthesize_pr_description`: Synthesizes the PR description.
- `vivarium.scout.git_analyzer.get_current_branch`: Gets the current branch.
- `vivarium.scout.git_analyzer.get_default_base_ref`: Gets the default base reference.
- `vivarium.scout.git_analyzer.get_upstream_ref`: Gets the upstream reference.
- `vivarium.scout.git_analyzer.has_remote_origin`: Checks if the repository has a remote origin.
- `vivarium.scout.git_analyzer.is_remote_empty`: Checks if the remote repository is empty.
- `vivarium.scout.git_drafts.assemble_pr_description`: Assembles the PR description from drafts.
- `vivarium.scout.git_drafts.assemble_pr_description_from_docs`: Assembles the PR description from docs.

## Potential Considerations
The function handles various edge cases and errors:
- Checks if the GitHub CLI is installed before running `gh` commands.
- Handles errors when running external commands, such as `git` and `gh`.
- Checks if the repository has a remote origin and if it's empty.
- Handles the case where the branch is detached or doesn't exist.
- Uses `try`-`except` blocks to catch and handle exceptions.
- Uses `finally` blocks to ensure that temporary files are deleted.

Performance considerations:
- The function uses `subprocess.run` to run external commands, which can be slower than using native Python functions.
- The function reads and writes files, which can be slow for large files or repositories.

## Signature
```python
def _cmd_pr(args: argparse.Namespace) -> int:
```
The function takes an `args` object of type `argparse.Namespace` and returns an integer. The `args` object is expected to contain various attributes, such as `from_docs`, `files`, `base_branch`, `create`, and `auto_draft`, which are used to determine the function's behavior.
---

# main

## Logic Overview
The `main` function serves as the entry point for the scout root CLI. It initializes an `ArgumentParser` instance and defines subparsers for three commands: `commit`, `pr`, and `status`. The function then parses the command-line arguments and executes the corresponding command based on the `command` argument. The main steps are:
1. Initialize the `ArgumentParser` and define subparsers.
2. Parse the command-line arguments using `parser.parse_args()`.
3. Execute the corresponding command based on the `command` argument:
   - For `commit`, call `_cmd_commit(args)`.
   - For `pr`, call `_cmd_pr(args)`.
   - For `status`, import `run_status` from `vivarium.scout.cli.status` and print the result of `run_status(Path.cwd().resolve())`.
4. If no valid command is provided, print the help message using `parser.print_help()`.

## Dependency Interactions
The `main` function interacts with the following dependencies:
- `argparse.ArgumentParser`: Creates an instance to parse command-line arguments.
- `argparse.ArgumentParser.add_subparsers`: Adds subparsers for the `commit`, `pr`, and `status` commands.
- `subparsers.add_parser`: Adds individual parsers for each command.
- `commit_parser.add_argument` and `pr_parser.add_argument`: Add arguments to the `commit` and `pr` parsers, respectively.
- `parser.parse_args`: Parses the command-line arguments.
- `parser.print_help`: Prints the help message if no valid command is provided.
- `_cmd_commit` and `_cmd_pr`: Calls these functions to execute the `commit` and `pr` commands, respectively.
- `vivarium.scout.cli.status.run_status`: Imports and calls this function to execute the `status` command.
- `pathlib.Path.cwd`: Uses the current working directory to resolve the path for the `status` command.
- `print`: Prints the result of the `status` command.

## Potential Considerations
Based on the code, some potential considerations include:
- Error handling: The code does not explicitly handle errors that may occur during the execution of the commands. It relies on the functions called by the commands (e.g., `_cmd_commit`, `_cmd_pr`, `run_status`) to handle errors.
- Edge cases: The code does not explicitly handle edge cases, such as invalid command-line arguments or missing dependencies.
- Performance: The code does not appear to have any significant performance concerns, as it primarily involves parsing command-line arguments and executing functions.

## Signature
The `main` function is defined with the following signature:
```python
def main() -> int:
```
This indicates that the function takes no arguments and returns an integer value. The return value is used to indicate the exit status of the program. In this case, the function returns 0 to indicate successful execution.