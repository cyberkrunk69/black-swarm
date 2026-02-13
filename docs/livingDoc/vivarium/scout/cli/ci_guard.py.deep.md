# DEFAULT_BASE_BRANCH

## Logic Overview
### Explanation of the Code's Flow and Main Steps

The given Python constant `DEFAULT_BASE_BRANCH` is assigned a string value `"origin/main"`. This constant does not contain any conditional statements, loops, or functions that would alter its value based on external factors. It is a simple assignment of a default base branch name to a constant variable.

### Main Steps

1. The code assigns the string `"origin/main"` to the constant `DEFAULT_BASE_BRANCH`.
2. The assignment is a one-time operation and does not involve any dynamic calculations or external dependencies.

## Dependency Interactions
### Explanation of How it Uses the Listed Dependencies

The given constant `DEFAULT_BASE_BRANCH` does not directly interact with the listed dependencies (`vivarium/scout/audit.py`, `vivarium/scout/git_analyzer.py`, `vivarium/scout/ignore.py`). However, it is likely used within these dependencies to provide a default base branch name for Git-related operations.

### Potential Interactions

1. The constant `DEFAULT_BASE_BRANCH` might be used as a default value in functions or methods within the listed dependencies.
2. It could be used to initialize variables or data structures within these dependencies.

## Potential Considerations
### Edge Cases, Error Handling, and Performance Notes

1. **Error Handling**: The code does not contain any error handling mechanisms. If the constant is used in a context where it is expected to be a valid Git branch, and it is not, it could lead to errors or unexpected behavior.
2. **Performance**: The assignment of the constant is a simple operation and does not have any significant performance implications.
3. **Edge Cases**: The constant assumes that the default base branch is always `"origin/main"`. If this is not the case, it could lead to incorrect behavior or errors.

## Signature
### N/A

Since the constant `DEFAULT_BASE_BRANCH` is not a function or method, it does not have a signature in the classical sense. However, if we were to consider it as a function, its signature would be:

```python
def DEFAULT_BASE_BRANCH():
    return "origin/main"
```
---

# DEFAULT_HOURLY_SPEND_LIMIT

## Logic Overview
### Explanation of the Code's Flow and Main Steps

The provided Python code defines a constant named `DEFAULT_HOURLY_SPEND_LIMIT` with a value of `5.0`. This constant does not have any associated logic or functionality; it simply assigns a value to a variable.

The code does not contain any conditional statements, loops, or functions that would alter its behavior based on input or external factors. The value of `DEFAULT_HOURLY_SPEND_LIMIT` is a fixed number that can be used throughout the codebase.

### Main Steps

1. The code defines a constant `DEFAULT_HOURLY_SPEND_LIMIT`.
2. The constant is assigned a value of `5.0`.

## Dependency Interactions
### Explanation of How the Code Uses the Listed Dependencies

The provided code does not directly interact with the listed dependencies (`vivarium/scout/audit.py`, `vivarium/scout/git_analyzer.py`, `vivarium/scout/ignore.py`). These dependencies are likely used elsewhere in the codebase, but they are not referenced or utilized in the code snippet provided.

However, it is possible that the `DEFAULT_HOURLY_SPEND_LIMIT` constant is used in conjunction with these dependencies in other parts of the codebase. Without more context or information, it is difficult to determine the exact nature of the interactions.

## Potential Considerations
### Edge Cases, Error Handling, and Performance Notes

1. **Error Handling**: The code does not contain any error handling mechanisms. If the value of `DEFAULT_HOURLY_SPEND_LIMIT` is not a number, it may cause a `TypeError` when used in mathematical operations.
2. **Performance**: The code does not have any performance-critical sections. The assignment of a constant value is a simple operation that does not impact performance.
3. **Edge Cases**: The code does not handle edge cases such as negative values or non-numeric inputs. If these cases are not handled elsewhere in the codebase, they may cause errors or unexpected behavior.

## Signature
### N/A

Since the code defines a constant, it does not have a signature in the classical sense. However, if we were to consider the constant as a function that returns a value, its signature would be:

```python
DEFAULT_HOURLY_SPEND_LIMIT: float = 5.0
```

This signature indicates that the constant returns a floating-point number (`float`) with a value of `5.0`.
---

# DEFAULT_MIN_CONFIDENCE

## Logic Overview
### Explanation of the Code's Flow and Main Steps

The provided Python constant `DEFAULT_MIN_CONFIDENCE` is assigned a value of `0.7`. This constant does not have any logic flow or main steps as it is a simple assignment of a value to a variable. The purpose of this constant is likely to be used as a default minimum confidence threshold in a machine learning or computer vision application.

### No Conditional Statements or Loops

There are no conditional statements (if-else) or loops (for, while) in this code snippet. The constant is directly assigned a value, and there are no dependencies or external functions being called.

### No Function Calls

There are no function calls in this code snippet. The constant is defined at the top-level scope, and there are no function definitions or calls.

## Dependency Interactions
### How Does it Use the Listed Dependencies?

The provided code snippet does not directly use the listed dependencies (`vivarium/scout/audit.py`, `vivarium/scout/git_analyzer.py`, `vivarium/scout/ignore.py`). These dependencies are likely used elsewhere in the codebase, but they are not relevant to the definition of the `DEFAULT_MIN_CONFIDENCE` constant.

### No Import Statements

There are no import statements in this code snippet. The dependencies listed are likely imported elsewhere in the codebase, but they are not used in this specific constant definition.

## Potential Considerations
### Edge Cases, Error Handling, Performance Notes

* **Edge Cases:** The value of `DEFAULT_MIN_CONFIDENCE` is a fixed value of `0.7`. There are no edge cases or special considerations for this value.
* **Error Handling:** There is no error handling in this code snippet. The constant is simply assigned a value, and there are no checks for potential errors.
* **Performance Notes:** The definition of this constant does not have any performance implications. It is a simple assignment of a value to a variable.

## Signature
### N/A

Since this is a constant definition, there is no function signature to analyze. The constant is simply assigned a value, and there are no parameters or return types to consider.
---

# _check_tldr_coverage

## Logic Overview
### Code Flow and Main Steps

The `_check_tldr_coverage` function checks if all `.py` files in a repository have a corresponding `.tldr.md` file in the `.docs` directory, unless the file is ignored. Here's a step-by-step breakdown of the code's flow:

1. **Initialization**: The function initializes an empty list `errors` to store any missing `.tldr.md` files.
2. **Loop through changed `.py` files**: The function iterates over the list of changed `.py` files (`changed_py`).
3. **Check if file is ignored**: For each file, it checks if the file is ignored using the `ignore.matches` method. If the file is ignored, it skips to the next iteration.
4. **Construct `.tldr.md` file path**: If the file is not ignored, it constructs the path to the corresponding `.tldr.md` file by joining the parent directory of the `.py` file with the `.docs` directory and the file name with a `.tldr.md` extension.
5. **Check if `.tldr.md` file exists**: It checks if the constructed `.tldr.md` file exists using the `exists` method. If it does not exist, it appends an error message to the `errors` list.
6. **Handle relative path exception**: If the file is not a direct child of the repository root, it tries to get the relative path of the file using the `relative_to` method. If this fails, it uses the original file path.
7. **Return result**: Finally, the function returns a tuple containing a boolean indicating whether there are any errors and the list of error messages.

## Dependency Interactions
### How it uses the listed dependencies

The `_check_tldr_coverage` function uses the following dependencies:

* `vivarium/scout/audit.py`: Not explicitly used in the code snippet.
* `vivarium/scout/git_analyzer.py`: Not explicitly used in the code snippet.
* `vivarium/scout/ignore.py`: The `ignore` object is used to check if a file is ignored using the `matches` method.

## Potential Considerations
### Edge cases, error handling, performance notes

Here are some potential considerations:

* **Error handling**: The function catches a `ValueError` exception when trying to get the relative path of a file. However, it does not handle other potential exceptions that may occur during file operations (e.g., permission errors).
* **Performance**: The function iterates over the list of changed `.py` files, which may be large. It would be more efficient to use a set or a dictionary to store the files and their corresponding `.tldr.md` files, rather than iterating over the list.
* **Ignored files**: The function ignores files based on the `ignore` object. However, it does not handle the case where a file is ignored but its corresponding `.tldr.md` file exists. It would be more robust to check if the `.tldr.md` file exists before ignoring the file.
* **Repository root**: The function assumes that the repository root is a valid directory. However, it does not check if the repository root exists or is a directory. It would be more robust to add error handling for these cases.

## Signature
### Function signature and return type

```python
def _check_tldr_coverage(
    repo_root: Path,
    changed_py: List[Path],
    ignore: IgnorePatterns,
) -> Tuple[bool, List[str]]:
```

The function takes three arguments:

* `repo_root`: The root directory of the repository (type: `Path`).
* `changed_py`: A list of changed `.py` files (type: `List[Path]`).
* `ignore`: An object that defines ignored files and directories (type: `IgnorePatterns`).

The function returns a tuple containing a boolean indicating whether there are any errors and a list of error messages (type: `Tuple[bool, List[str]]`).
---

# _check_draft_confidence

## Logic Overview
### Step-by-Step Breakdown

The `_check_draft_confidence` function checks if there are any draft/nav events in the audit log within the last N hours that have a confidence level below a specified minimum confidence. Here's a step-by-step explanation of the code's flow:

1. **Initialization**: The function initializes an empty list `errors` to store any issues found during the audit.
2. **Timeframe Setup**: It calculates the time `since` by subtracting the specified number of hours (`hours`) from the current time (`datetime.now(timezone.utc)`).
3. **Audit Query**: The function queries the audit log using the `audit.query` method, passing the `since` time as a parameter. This retrieves a list of events that occurred within the specified timeframe.
4. **Event Loop**: The function iterates over each event in the `events` list.
5. **Event Type Check**: For each event, it checks if the event type is either "nav", "commit_draft", or "pr_snippet". If not, it skips to the next event.
6. **Confidence Check**: It retrieves the confidence value from the event and checks if it's not `None`. If it is, it skips to the next event.
7. **Confidence Normalization**: If the confidence value is an integer or float greater than 1, it normalizes the value by dividing it by 100.0.
8. **Error Detection**: If the normalized confidence value is an integer or float and is less than the specified minimum confidence, it appends an error message to the `errors` list.
9. **Return**: Finally, the function returns a tuple containing a boolean indicating whether any errors were found (`len(errors) == 0`) and the list of error messages (`errors`).

## Dependency Interactions
### Vivarium Scout Dependencies

The `_check_draft_confidence` function interacts with the following Vivarium Scout dependencies:

* `audit.py`: The function uses the `audit.query` method to retrieve events from the audit log.
* `git_analyzer.py`: Not directly used in this function, but potentially used in the `audit` module.
* `ignore.py`: Not directly used in this function, but potentially used in the `audit` module.

## Potential Considerations
### Edge Cases and Error Handling

* **Invalid input**: The function does not handle invalid input types for `audit`, `min_confidence`, or `hours`. It assumes that `audit` is an instance of `AuditLog`, `min_confidence` is a float, and `hours` is an integer.
* **Zero hours**: If `hours` is set to 0, the function will return an empty list of events, but it may not be the expected behavior.
* **Negative hours**: If `hours` is set to a negative value, the function will raise a `ValueError` when calculating the `since` time.
* **Large audit logs**: If the audit log is very large, the function may take a long time to execute or even run out of memory.

## Signature
### Function Signature

```python
def _check_draft_confidence(
    audit: AuditLog,
    min_confidence: float,
    hours: int = 24,
) -> Tuple[bool, List[str]]:
```

This function takes three parameters:

* `audit`: An instance of `AuditLog` representing the audit log to query.
* `min_confidence`: A float representing the minimum confidence level to check for.
* `hours`: An integer representing the number of hours to look back in the audit log (default is 24).

The function returns a tuple containing a boolean indicating whether any errors were found and a list of error messages.
---

# _check_hourly_spend

## Logic Overview
### Code Flow and Main Steps

The `_check_hourly_spend` function is designed to check if the hourly spend of an `AuditLog` object is less than a specified `limit`. Here's a step-by-step breakdown of the code's flow:

1. **Get Hourly Spend**: The function calls `audit.hourly_spend(hours=1)` to retrieve the hourly spend of the `AuditLog` object.
2. **Compare Spend to Limit**: It then checks if the retrieved spend is greater than or equal to the specified `limit`.
3. **Return Result**: Based on the comparison, the function returns a tuple containing a boolean value (`ok`) and a list of error messages (`errors`).

### Conditional Logic

The code uses a simple conditional statement to determine the return value:

```python
if spend >= limit:
    return (False, [f"Hourly spend ${spend:.2f} >= limit ${limit:.2f}"])
```

If the spend is greater than or equal to the limit, the function returns `False` and a list containing an error message. Otherwise, it returns `True` and an empty list.

## Dependency Interactions
### Interaction with vivarium/scout/audit.py

The `_check_hourly_spend` function interacts with the `AuditLog` class from `vivarium/scout/audit.py`. Specifically, it calls the `hourly_spend` method on the `AuditLog` object to retrieve the hourly spend.

### Interaction with vivarium/scout/git_analyzer.py and vivarium/scout/ignore.py

There is no direct interaction with `vivarium/scout/git_analyzer.py` and `vivarium/scout/ignore.py` in the provided code. These dependencies are likely included for other parts of the codebase.

## Potential Considerations
### Edge Cases

* What if the `AuditLog` object does not have an `hourly_spend` method? The code will raise an `AttributeError`.
* What if the `limit` is not a positive number? The code will still work as intended, but it may not be the expected behavior.

### Error Handling

* The code does not handle any exceptions that may be raised by the `hourly_spend` method. It assumes that the method will always return a valid value.

### Performance Notes

* The code uses a simple conditional statement, which is efficient in terms of performance.
* However, if the `AuditLog` object has a large number of records, the `hourly_spend` method may take a significant amount of time to execute. This could impact the performance of the `_check_hourly_spend` function.

## Signature
### Function Signature

```python
def _check_hourly_spend(
    audit: AuditLog,
    limit: float,
) -> Tuple[bool, List[str]]:
```
---

# _check_draft_events_recent

## Logic Overview
### Code Flow and Main Steps

The `_check_draft_events_recent` function is designed to check if there are any `commit_draft` events in the last N hours within an audit log. Here's a step-by-step breakdown of the code's flow:

1. **Calculate the time threshold**: The function calculates the time threshold `since` by subtracting the specified number of hours (`hours`) from the current time (`datetime.now(timezone.utc)`).
2. **Query audit events**: The function uses the `audit.query` method to retrieve events that occurred after the calculated time threshold (`since`).
3. **Check for commit_draft events**: The function checks if any of the retrieved events have an `event` key with a value of `"commit_draft"` using the `any` function with a generator expression.
4. **Return result**: If no `commit_draft` events are found, the function returns a tuple containing `False` and a list with a message indicating that the draft system may be broken. Otherwise, it returns a tuple containing `True` and an empty list.

## Dependency Interactions
### How the Code Uses the Listed Dependencies

The `_check_draft_events_recent` function interacts with the following dependencies:

* `vivarium/scout/audit.py`: The `audit` object is used to query events using the `audit.query` method.
* `vivarium/scout/git_analyzer.py`: Not explicitly used in the code, but potentially used by the `audit` object.
* `vivarium/scout/ignore.py`: Not explicitly used in the code.

The function relies on the `audit` object to retrieve events from the audit log, which is likely implemented in the `vivarium/scout/audit.py` module.

## Potential Considerations
### Edge Cases, Error Handling, and Performance Notes

The code has the following potential considerations:

* **Error handling**: The function does not handle potential errors that may occur when querying the audit log or accessing the `event` key in the events dictionary. Consider adding try-except blocks to handle these errors.
* **Performance**: The function uses the `any` function with a generator expression to check for `commit_draft` events. This may be inefficient for large numbers of events. Consider using a more efficient data structure or algorithm to improve performance.
* **Input validation**: The function assumes that the `audit` object is valid and has a `query` method. Consider adding input validation to ensure that the `audit` object is valid before using it.
* **Timezone handling**: The function uses the `timezone.utc` timezone to calculate the time threshold. Consider using a more robust timezone handling approach to account for different timezones.

## Signature
### Function Signature

```python
def _check_draft_events_recent(
    audit: AuditLog,
    hours: int = 24,
) -> Tuple[bool, List[str]]:
```
---

# run_ci_guard

## Logic Overview
The `run_ci_guard` function is designed to run a series of checks on a repository to ensure it meets certain criteria. The function takes several parameters, including the repository root, base branch, hourly limit, minimum confidence, and whether to require draft events. It returns a tuple containing a boolean indicating whether all checks passed and a list of error messages.

Here's a step-by-step breakdown of the function's flow:

1. **Initialization**: The function initializes an empty list `errors` to store any error messages that occur during the checks.
2. **Get Changed Files**: The function attempts to get a list of changed files in the repository using the `get_changed_files` function. If this fails, it tries again without specifying a base branch. If both attempts fail, it returns a failure message.
3. **Filter Changed Files**: The function filters the list of changed files to only include Python files.
4. **Check TLDR Coverage**: The function calls the `_check_tldr_coverage` function to check the TLDR (Too Long; Didn't Read) coverage of the changed Python files. If this check fails, it adds any error messages to the `errors` list.
5. **Check Draft Confidence**: The function calls the `_check_draft_confidence` function to check the confidence of the draft events in the audit log. If this check fails, it adds any error messages to the `errors` list.
6. **Check Hourly Spend**: The function calls the `_check_hourly_spend` function to check the hourly spend of the audit log. If this check fails, it adds any error messages to the `errors` list.
7. **Check Draft Events (if required)**: If the `require_draft_events` parameter is `True`, the function calls the `_check_draft_events_recent` function to check if there are any draft events in the audit log within the specified time period. If this check fails, it adds any error messages to the `errors` list.
8. **Return Result**: Finally, the function returns a tuple containing a boolean indicating whether all checks passed (`len(errors) == 0`) and the list of error messages.

## Dependency Interactions
The `run_ci_guard` function interacts with the following dependencies:

* `vivarium/scout/audit.py`: This module is used to access the audit log, which contains information about the repository's activity.
* `vivarium/scout/git_analyzer.py`: This module is used to get a list of changed files in the repository.
* `vivarium/scout/ignore.py`: This module is used to create an `IgnorePatterns` object, which is used to filter out ignored files.

The function calls the following functions from these dependencies:

* `_check_tldr_coverage` (from `vivarium/scout/audit.py`)
* `_check_draft_confidence` (from `vivarium/scout/audit.py`)
* `_check_hourly_spend` (from `vivarium/scout/audit.py`)
* `_check_draft_events_recent` (from `vivarium/scout/audit.py`)
* `get_changed_files` (from `vivarium/scout/git_analyzer.py`)
* `IgnorePatterns` (from `vivarium/scout/ignore.py`)

## Potential Considerations
Here are some potential considerations for the `run_ci_guard` function:

* **Error Handling**: The function catches exceptions when getting changed files and returns a failure message. However, it does not catch exceptions when calling the other functions from the dependencies. It may be worth adding try-except blocks to handle these exceptions.
* **Performance**: The function calls several functions from the dependencies, which may have performance implications. It may be worth profiling the function to identify any performance bottlenecks.
* **Edge Cases**: The function assumes that the `require_draft_events` parameter is a boolean. However, it does not check for this. It may be worth adding a check to ensure that this parameter is a boolean.
* **Input Validation**: The function does not validate the input parameters. It may be worth adding checks to ensure that the parameters are valid.

## Signature
```python
def run_ci_guard(
    repo_root: Path,
    base_branch: str = DEFAULT_BASE_BRANCH,
    hourly_limit: float = DEFAULT_HOURLY_SPEND_LIMIT,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    require_draft_events: bool = False,
    draft_events_hours: int = 24,
) -> Tuple[bool, List[str]]:
```
This signature defines the function `run_ci_guard` with the following parameters:

* `repo_root`: The root of the repository (a `Path` object)
* `base_branch`: The base branch to use (a string, defaulting to `DEFAULT_BASE_BRANCH`)
* `hourly_limit`: The hourly spend limit (a float, defaulting to `DEFAULT_HOURLY_SPEND_LIMIT`)
* `min_confidence`: The minimum confidence required (a float, defaulting to `DEFAULT_MIN_CONFIDENCE`)
* `require_draft_events`: Whether to require draft events (a boolean, defaulting to `False`)
* `draft_events_hours`: The number of hours to check for draft events (an integer, defaulting to 24)

The function returns a tuple containing a boolean indicating whether all checks passed and a list of error messages.
---

# main

## Logic Overview
### Main Steps

The `main` function serves as the CLI entry point for the `scout-ci-guard` application. It's responsible for parsing command-line arguments, running the CI validation, and returning an exit code based on the outcome.

Here's a step-by-step breakdown of the code's flow:

1. **Argument Parsing**: The function uses the `argparse` library to define and parse command-line arguments. It expects the following options:
	* `--base-branch`: The base branch for diff (default: `DEFAULT_BASE_BRANCH`).
	* `--hourly-limit`: The maximum hourly spend in USD (default: `DEFAULT_HOURLY_SPEND_LIMIT`).
	* `--min-confidence`: The minimum confidence for drafts (default: `DEFAULT_MIN_CONFIDENCE`).
	* `--require-draft-events`: A flag to fail if no commit_draft events are found in the audit (last 24h).
	* `--draft-events-hours`: The number of hours to look back for commit_draft events (default: 24).
2. **CI Validation**: The function calls the `run_ci_guard` function, passing the parsed arguments as keyword arguments. This function is not shown in the provided code snippet, but it's likely responsible for performing the actual CI validation.
3. **Error Handling**: If the CI validation fails, the function prints error messages to the standard error stream and returns a non-zero exit code (1).
4. **Success**: If the CI validation succeeds, the function returns a zero exit code (0).

## Dependency Interactions

The `main` function interacts with the following dependencies:

* `argparse`: Used for parsing command-line arguments.
* `vivarium/scout/audit.py`: Imported, but not directly used in the provided code snippet. It's likely used by the `run_ci_guard` function.
* `vivarium/scout/git_analyzer.py`: Imported, but not directly used in the provided code snippet. It's likely used by the `run_ci_guard` function.
* `vivarium/scout/ignore.py`: Imported, but not directly used in the provided code snippet. It's likely used by the `run_ci_guard` function.

## Potential Considerations

### Edge Cases

* The function assumes that the `run_ci_guard` function will return a tuple containing a boolean value (`ok`) and a list of error messages (`errors`). If this assumption is not met, the function may fail or produce unexpected results.
* The function does not handle cases where the `--require-draft-events` flag is set, but no commit_draft events are found in the audit. In such cases, the function will fail, but it may be desirable to provide additional information or guidance to the user.

### Error Handling

* The function prints error messages to the standard error stream, but it does not provide any additional information about the errors. It may be desirable to include more detailed error messages or to provide a way for the user to access the error information.
* The function returns a non-zero exit code (1) when an error occurs, but it does not provide any additional information about the exit code. It may be desirable to use a more specific exit code or to provide a way for the user to access the exit code information.

### Performance Notes

* The function uses the `argparse` library to parse command-line arguments, which can be slow for large numbers of arguments. It may be desirable to use a more efficient argument parsing library or to optimize the argument parsing process.
* The function calls the `run_ci_guard` function, which may perform expensive computations or I/O operations. It may be desirable to optimize the `run_ci_guard` function or to use caching or other techniques to improve performance.

## Signature

```python
def main() -> int:
    """CLI entry point."""
```