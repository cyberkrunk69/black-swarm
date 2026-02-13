# DEFAULT_BASE_BRANCH

## Logic Overview
The code defines a constant `DEFAULT_BASE_BRANCH` and assigns it the string value `"origin/main"`. This constant is not used within any conditional statements or loops in the provided code snippet. The main step is the assignment of the string value to the constant.

## Dependency Interactions
There are no traced calls to analyze. The code does not reference any qualified names from the imported modules (`vivarium/scout/audit.py`, `vivarium/scout/git_analyzer.py`, `vivarium/scout/ignore.py`).

## Potential Considerations
The constant `DEFAULT_BASE_BRANCH` is assigned a hardcoded string value. Potential considerations include:
- The hardcoded value may need to be updated if the base branch changes.
- There is no error handling for cases where the assigned branch does not exist.
- The performance impact of this constant is negligible since it is a simple assignment.

## Signature
N/A
---

# DEFAULT_HOURLY_SPEND_LIMIT

## Logic Overview
The code defines a constant `DEFAULT_HOURLY_SPEND_LIMIT` and assigns it a value of `5.0`. There are no conditional statements, loops, or functions in this code snippet, making it a simple declaration.

## Dependency Interactions
There are no traced calls in this code snippet. The imports from `vivarium/scout/audit.py`, `vivarium/scout/git_analyzer.py`, and `vivarium/scout/ignore.py` do not interact with the `DEFAULT_HOURLY_SPEND_LIMIT` constant in this specific code snippet.

## Potential Considerations
The code does not handle any potential errors or edge cases. Since it is a simple constant declaration, there is no performance consideration in this specific line of code. However, the value of `5.0` may have implications in the context of the larger program, but that cannot be determined from this snippet alone.

## Signature
N/A
---

# DEFAULT_MIN_CONFIDENCE

## Logic Overview
The code defines a constant `DEFAULT_MIN_CONFIDENCE` and assigns it a value of `0.7`. This constant is not used within the provided code snippet, but it is likely used elsewhere in the program to represent a minimum confidence threshold.

## Dependency Interactions
There are no traced calls to analyze. The code does not reference any qualified names from the imported modules (`vivarium/scout/audit.py`, `vivarium/scout/git_analyzer.py`, `vivarium/scout/ignore.py`).

## Potential Considerations
The code does not handle any potential errors or edge cases. The constant is defined with a fixed value, which may not be suitable for all scenarios. The performance of the code is not a concern, as it is a simple constant definition.

## Signature
N/A
---

# _check_tldr_coverage

## Logic Overview
The `_check_tldr_coverage` function iterates over a list of Python files (`changed_py`) and checks if each file has a corresponding `.tldr.md` file in a `.docs` directory. The function skips files that match the ignore patterns (`ignore`). If a `.tldr.md` file is missing, an error message is appended to the `errors` list. The function returns a tuple containing a boolean indicating whether any errors were found (`len(errors) == 0`) and the list of error messages.

## Dependency Interactions
The function interacts with the following dependencies:
- `ignore.matches(f, repo_root)`: checks if a file (`f`) matches the ignore patterns (`ignore`) relative to the repository root (`repo_root`).
- `f.relative_to(repo_root)`: gets the relative path of a file (`f`) to the repository root (`repo_root`).
- `tldr_path.exists()`: checks if a `.tldr.md` file exists at the specified path (`tldr_path`).
- `errors.append(...)`: appends an error message to the `errors` list.
- `len(errors)`: gets the number of error messages in the `errors` list.

## Potential Considerations
- The function handles the case where a file is not relative to the repository root by catching the `ValueError` exception and using the absolute path instead.
- The function does not handle any other exceptions that may occur when checking file existence or relative paths.
- The function assumes that the `.docs` directory exists for each file; if it does not, the `tldr_path.exists()` check will always return `False`.
- The function returns a tuple containing a boolean and a list of error messages, which may be useful for further processing or logging.

## Signature
The function signature is:
```python
def _check_tldr_coverage(
    repo_root: Path,
    changed_py: List[Path],
    ignore: IgnorePatterns,
) -> Tuple[bool, List[str]]:
```
This indicates that the function:
- Takes three parameters: `repo_root` (a `Path` object), `changed_py` (a list of `Path` objects), and `ignore` (an `IgnorePatterns` object).
- Returns a tuple containing two values: a boolean (`ok`) and a list of strings (`errors`). The boolean indicates whether any errors were found, and the list contains error messages for each missing `.tldr.md` file.
---

# _check_draft_confidence

## Logic Overview
The `_check_draft_confidence` function checks if there are any draft or navigation events in the audit log within a specified time frame that have a confidence level below a minimum threshold. The main steps are:
1. Calculate the time frame by subtracting a specified number of hours from the current time.
2. Query the audit log for events within this time frame.
3. Iterate over the events and check if the event type is "nav", "commit_draft", or "pr_snippet".
4. For each matching event, retrieve the confidence value and check if it's below the minimum threshold.
5. If the confidence value is below the threshold, add an error message to the list of errors.
6. Return a tuple containing a boolean indicating whether any errors were found and the list of error messages.

## Dependency Interactions
The function interacts with the following dependencies:
* `audit.query`: This is called to retrieve events from the audit log within the specified time frame.
* `datetime.datetime.now`: This is called to get the current time.
* `datetime.timedelta`: This is used to calculate the time frame by subtracting a specified number of hours from the current time.
* `errors.append`: This is called to add error messages to the list of errors.
* `isinstance`: This is used to check the type of the confidence value.
* `len`: This is called to check if the list of errors is empty.
* `obj.get`: This is called to retrieve the event type and confidence value from each event object.

## Potential Considerations
Some potential considerations based on the code are:
* The function assumes that the confidence value is either an integer or a float, and that it's greater than 1 if it's an integer (in which case it's divided by 100). If the confidence value is in a different format, this could cause issues.
* The function doesn't handle any exceptions that might be raised by the `audit.query` call or other dependencies.
* The function uses a simple linear scan to iterate over the events, which could be inefficient if the number of events is very large.
* The function returns a tuple containing a boolean and a list of error messages. If the list of error messages is very large, this could use a significant amount of memory.

## Signature
The function signature is:
```python
def _check_draft_confidence(audit: AuditLog, min_confidence: float, hours: int=24) -> Tuple[bool, List[str]]:
```
This indicates that the function takes three parameters:
* `audit`: an `AuditLog` object
* `min_confidence`: a float representing the minimum confidence threshold
* `hours`: an integer representing the number of hours to look back in the audit log (defaulting to 24 if not specified)
The function returns a tuple containing two values:
* A boolean indicating whether any errors were found
* A list of strings representing the error messages (if any)
---

# _check_hourly_spend

## Logic Overview
The `_check_hourly_spend` function takes an `audit` object of type `AuditLog` and a `limit` of type `float` as input. It calculates the hourly spend by calling the `hourly_spend` method on the `audit` object with `hours=1`. The function then checks if the calculated spend is greater than or equal to the provided limit. If it is, the function returns a tuple containing `False` and a list with an error message. If the spend is less than the limit, the function returns a tuple containing `True` and an empty list.

## Dependency Interactions
The function interacts with the `audit` object by calling its `hourly_spend` method, which is qualified as `audit.hourly_spend`. This method is used to calculate the hourly spend. The function does not directly interact with the imported modules (`vivarium/scout/audit.py`, `vivarium/scout/git_analyzer.py`, `vivarium/scout/ignore.py`), but it uses the `AuditLog` type from one of these modules.

## Potential Considerations
The function does not handle any potential errors that might occur when calling the `hourly_spend` method. If this method raises an exception, it will not be caught or handled by the `_check_hourly_spend` function. Additionally, the function assumes that the `hourly_spend` method returns a value that can be compared to the `limit` using the `>=` operator. If this is not the case, the function may raise a `TypeError`. The function also does not check if the `limit` is a valid value (e.g., non-negative).

## Signature
The function signature is `def _check_hourly_spend(audit: AuditLog, limit: float) -> Tuple[bool, List[str]]`. This indicates that the function:
- Takes two parameters: `audit` of type `AuditLog` and `limit` of type `float`.
- Returns a tuple containing two values: a boolean and a list of strings.
The use of the `AuditLog` type and the `float` type for the `limit` parameter suggests that the function is designed to work with a specific type of audit log data and a specific type of limit value. The return type of `Tuple[bool, List[str]]` indicates that the function will return a boolean value indicating whether the hourly spend is within the limit, along with a list of error messages if the spend exceeds the limit.
---

# _check_draft_events_recent

## Logic Overview
The `_check_draft_events_recent` function checks if there are any "commit_draft" events in the audit log within a specified time frame (default is 24 hours). The main steps are:
1. Calculate the time frame by subtracting the specified number of hours from the current time.
2. Query the audit log for events that occurred within this time frame.
3. Check if any of these events are "commit_draft" events.
4. Return a boolean indicating whether any "commit_draft" events were found, along with a list of error messages (if any).

## Dependency Interactions
The function interacts with the following dependencies:
- `datetime.datetime.now`: used to get the current time.
- `datetime.timedelta`: used to calculate the time frame by subtracting the specified number of hours from the current time.
- `audit.query`: used to query the audit log for events within the specified time frame.
- `any`: used to check if any of the events in the audit log are "commit_draft" events.
- `e.get`: used to access the "event" field of each event in the audit log.

## Potential Considerations
Based on the code, some potential considerations are:
- The function does not handle any exceptions that may occur when querying the audit log or accessing event fields.
- The function assumes that the audit log is properly configured and available.
- The function uses a default time frame of 24 hours, which may not be suitable for all use cases.
- The function returns a list of error messages, but only includes a single error message if no "commit_draft" events are found.
- The performance of the function may be affected by the size of the audit log and the number of events within the specified time frame.

## Signature
The function signature is:
```python
def _check_draft_events_recent(audit: AuditLog, hours: int = 24) -> Tuple[bool, List[str]]:
```
This indicates that the function:
- Takes two parameters: `audit` of type `AuditLog` and `hours` of type `int` (with a default value of 24).
- Returns a tuple containing two values: a boolean and a list of strings. The boolean indicates whether any "commit_draft" events were found, and the list of strings contains error messages (if any).
---

# run_ci_guard

## Logic Overview
The `run_ci_guard` function is designed to run a series of checks on a repository. The main steps are:
1. Resolve the repository root path.
2. Get the list of changed files in the repository.
3. Filter the changed files to only include Python files.
4. Initialize an `IgnorePatterns` object to ignore certain files.
5. Run the following checks:
   - `_check_tldr_coverage` to check the coverage of TLDR files.
   - `_check_draft_confidence` to check the confidence of draft events.
   - `_check_hourly_spend` to check the hourly spend.
   - `_check_draft_events_recent` to check for recent draft events (if `require_draft_events` is `True`).
6. Close the audit log and return a tuple containing a boolean indicating whether all checks passed and a list of error messages.

## Dependency Interactions
The `run_ci_guard` function interacts with the following dependencies:
- `vivarium.scout.git_analyzer.get_changed_files`: to get the list of changed files in the repository.
- `vivarium.scout.ignore.IgnorePatterns`: to ignore certain files.
- `vivarium.scout.audit.AuditLog`: to log audit events.
- `_check_tldr_coverage`, `_check_draft_confidence`, `_check_hourly_spend`, and `_check_draft_events_recent`: to run the various checks.
- `pathlib.Path`: to work with file paths.
- `len`: to get the length of the error list.
- `errors.extend`: to add error messages to the list.

## Potential Considerations
The code handles the following edge cases and considerations:
- If an exception occurs while getting the changed files, it tries to get the changed files again without the `base_branch` parameter. If this also fails, it returns an error message.
- If the `require_draft_events` parameter is `True`, it checks for recent draft events.
- The function uses a try-except block to catch any exceptions that may occur while getting the changed files.
- The function closes the audit log after all checks have been run.
- The function returns a tuple containing a boolean indicating whether all checks passed and a list of error messages.

## Signature
The `run_ci_guard` function has the following signature:
```python
def run_ci_guard(
    repo_root: Path,
    base_branch: str = DEFAULT_BASE_BRANCH,
    hourly_limit: float = DEFAULT_HOURLY_SPEND_LIMIT,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    require_draft_events: bool = False,
    draft_events_hours: int = 24
) -> Tuple[bool, List[str]]:
```
This signature indicates that the function:
- Takes six parameters: `repo_root`, `base_branch`, `hourly_limit`, `min_confidence`, `require_draft_events`, and `draft_events_hours`.
- Returns a tuple containing two values: a boolean indicating whether all checks passed and a list of error messages.
- Uses the following types: `Path`, `str`, `float`, `bool`, `int`, and `Tuple[bool, List[str]]`.
---

# main

## Logic Overview
The `main` function serves as the CLI entry point. It can be broken down into the following main steps:
1. **Argument Parsing**: The function initializes an `ArgumentParser` and defines several command-line arguments, including `--base-branch`, `--hourly-limit`, `--min-confidence`, `--require-draft-events`, and `--draft-events-hours`.
2. **Parsing Arguments**: It then parses the command-line arguments using `parser.parse_args()`.
3. **Running CI Guard**: The function calls `run_ci_guard` with the parsed arguments and the current working directory as the repository root.
4. **Error Handling and Return**: If `run_ci_guard` returns an error (i.e., `ok` is `False`), it prints the errors to the standard error stream and returns an exit code of 1. Otherwise, it returns 0.

## Dependency Interactions
The `main` function interacts with the following traced calls:
* `argparse.ArgumentParser`: Creates a new argument parser with a specified program name and description.
* `parser.add_argument`: Adds command-line arguments to the parser, including their names, types, default values, and help messages.
* `parser.parse_args`: Parses the command-line arguments and returns a namespace containing the parsed values.
* `pathlib.Path.cwd`: Gets the current working directory, which is used as the repository root for `run_ci_guard`.
* `print`: Prints error messages to the standard error stream if `run_ci_guard` returns an error.
* `run_ci_guard`: Calls the `run_ci_guard` function with the parsed arguments and repository root.

## Potential Considerations
Based on the code, the following potential considerations can be identified:
* **Error Handling**: The function handles errors returned by `run_ci_guard` by printing them to the standard error stream and returning a non-zero exit code.
* **Performance**: The function's performance may depend on the performance of `run_ci_guard`, which is not shown in the provided code.
* **Edge Cases**: The function does not appear to handle any specific edge cases, such as invalid command-line arguments or repository root issues. However, `argparse` may handle some of these cases automatically.

## Signature
The `main` function has the following signature:
```python
def main() -> int:
```
This indicates that the function takes no arguments and returns an integer value, which is typically used as an exit code in CLI applications. The return type is explicitly specified as `int`.