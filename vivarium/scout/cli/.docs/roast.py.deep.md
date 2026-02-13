# PERIOD_TODAY

## Logic Overview
The code defines a constant `PERIOD_TODAY` and assigns it the string value `"today"`. There are no conditional statements, loops, or function calls in this code snippet. The main step is the assignment of the string value to the constant.

## Dependency Interactions
The code does not use any of the traced calls. The imports from `vivarium/scout/audit.py`, `vivarium/scout/config.py`, and `vivarium/scout/llm.py` are not referenced in this specific code snippet.

## Potential Considerations
There are no edge cases or error handling mechanisms in this code snippet, as it is a simple assignment of a string value to a constant. The performance impact of this code is negligible, as it only involves a single assignment operation. 

## Signature
N/A
---

# PERIOD_WEEK

## Logic Overview
The code defines a constant `PERIOD_WEEK` and assigns it the string value `"week"`. There are no conditional statements, loops, or functions in this code snippet, making it a straightforward assignment.

## Dependency Interactions
The code does not use any of the traced calls. The imports from `vivarium/scout/audit.py`, `vivarium/scout/config.py`, and `vivarium/scout/llm.py` are not referenced in this specific code snippet.

## Potential Considerations
There are no edge cases or error handling mechanisms in this code. The assignment of a string value to a constant is a simple operation and does not pose any performance concerns. The constant `PERIOD_WEEK` can be used elsewhere in the codebase, but its usage is not traced in this snippet.

## Signature
N/A
---

# PERIOD_MONTH

## Logic Overview
The code defines a constant `PERIOD_MONTH` and assigns it the string value `"month"`. There are no conditional statements, loops, or functions in this code snippet, making it a straightforward assignment.

## Dependency Interactions
The code does not use any of the traced calls. The imports from `vivarium/scout/audit.py`, `vivarium/scout/config.py`, and `vivarium/scout/llm.py` are not utilized in this specific code snippet.

## Potential Considerations
There are no apparent edge cases or error handling mechanisms in this code. The assignment of a string value to a constant is a simple operation and does not pose any performance concerns. However, it is worth noting that the constant `PERIOD_MONTH` is not used within this code snippet, so its purpose and usage are not immediately clear.

## Signature
N/A
---

# DEFAULT_NAIVE_COST_PER_NAV

## Logic Overview
The code defines a constant `DEFAULT_NAIVE_COST_PER_NAV` and assigns it a value of `0.50`. This constant is not part of any conditional statement or loop, and its value is not modified anywhere in the provided code. The constant is simply defined and made available for potential use elsewhere in the program.

## Dependency Interactions
There are no traced calls, so the constant `DEFAULT_NAIVE_COST_PER_NAV` does not interact with any functions or methods. The imports from `vivarium/scout/audit.py`, `vivarium/scout/config.py`, and `vivarium/scout/llm.py` do not directly influence the definition or value of this constant.

## Potential Considerations
Since `DEFAULT_NAIVE_COST_PER_NAV` is a constant, its value is not expected to change. However, potential considerations include:
- The constant's value is a floating-point number, which may lead to precision issues in certain calculations.
- There is no error handling or validation for this constant, as it is simply defined and assigned a value.
- The performance impact of this constant is negligible, as it is a simple assignment and does not involve any computationally expensive operations.

## Signature
N/A
---

# _parse_archive_timestamp

## Logic Overview
The `_parse_archive_timestamp` function takes a string `name` as input and attempts to parse it into a datetime object in UTC. The main steps are:
1. Use a regular expression to match the input string against a specific pattern.
2. If the pattern matches, extract the matched groups and convert them to integers.
3. Use the extracted integers to create a datetime object with UTC timezone.
4. If any step fails, return `None`.

## Dependency Interactions
The function interacts with the following traced calls:
- `re.match`: used to match the input string against the pattern `r"audit_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})\.jsonl\.gz"`.
- `m.group`: used to extract the matched groups from the regular expression match object `m`.
- `int`: used to convert the extracted groups to integers.
- `datetime.datetime`: used to create a datetime object from the extracted integers.

## Potential Considerations
The function handles potential errors in the following ways:
- If the input string does not match the expected pattern, the function returns `None`.
- If the extracted groups cannot be converted to integers, or if the datetime object cannot be created, the function catches the `ValueError` or `TypeError` exception and returns `None`.
- The function uses a specific timezone (UTC) when creating the datetime object, which may be relevant for handling dates and times in different regions.
- The function does not appear to handle other potential edge cases, such as an input string that is `None` or empty.

## Signature
The function signature is `def _parse_archive_timestamp(name: str) -> Optional[datetime]`, which indicates that:
- The function takes a single argument `name` of type `str`.
- The function returns an object of type `Optional[datetime]`, which means it may return either a datetime object or `None`.
---

# _iter_archive_lines

## Logic Overview
The `_iter_archive_lines` function is designed to read a gzipped JSONL archive file and yield non-empty lines from it. The main steps involved in this process are:
1. Opening the gzipped file using `gzip.open`.
2. Iterating over each line in the file.
3. Removing trailing newline characters from each line using `line.rstrip`.
4. Checking if the line is not empty and appending it to the `lines` list if it's not empty.
5. Handling exceptions that may occur during this process, such as `OSError` or `gzip.BadGzipFile`.
6. Returning the list of non-empty lines.

## Dependency Interactions
The function interacts with the following dependencies:
- `gzip.open`: This is used to open the gzipped file in read mode (`"rt"`).
- `line.rstrip`: This is used to remove trailing newline characters (`"\n\r"`) from each line.
- `lines.append`: This is used to add non-empty lines to the `lines` list.
- `sys.stderr.write`: This is used to write error messages to the standard error stream when an exception occurs.

## Potential Considerations
Some potential considerations based on the code are:
- **Error Handling**: The function catches `OSError` and `gzip.BadGzipFile` exceptions, which may occur when opening or reading the gzipped file. If an exception occurs, an error message is written to the standard error stream, and the function continues execution.
- **Performance**: The function reads the entire file into memory by appending lines to the `lines` list. This could be a performance issue for large files.
- **Edge Cases**: The function assumes that the input file is a valid gzipped JSONL archive. If the file is not in the correct format, the function may not work as expected.

## Signature
The function signature is `def _iter_archive_lines(path: Path) -> List[str]`. This indicates that:
- The function takes a single argument `path` of type `Path`.
- The function returns a list of strings (`List[str]`).
- The function is intended to be private (due to the leading underscore in its name), suggesting it should not be used directly outside of the module where it is defined.
---

# load_audit_log

## Logic Overview
The `load_audit_log` function is designed to load audit events for a specified period from both current and archived logs. The main steps in the function's logic are:
1. Determine the `since` timestamp based on the provided `period`.
2. Initialize an empty list `events` to store the audit events.
3. Load audit events from the current audit log file if it exists.
4. Load audit events from archived log files if they exist.
5. Sort the collected events by their timestamp.
6. Return the sorted list of events.

## Dependency Interactions
The function interacts with various dependencies through the following traced calls:
- `_iter_archive_lines`: used to iterate over lines in archived log files.
- `_parse_archive_timestamp`: used to parse the timestamp from archived log file names.
- `datetime.datetime.now`: used to get the current date and time.
- `datetime.timedelta`: used to calculate the `since` timestamp based on the provided period.
- `e.get`: used to access the "ts" key in an event dictionary.
- `events.append`: used to add events to the `events` list.
- `events.sort`: used to sort the events by their timestamp.
- `json.loads`: used to parse JSON lines in archived log files.
- `log.close`: used to close the current audit log file after querying it.
- `log.query`: used to query the current audit log file for events since the `since` timestamp.
- `now.replace`: used to replace the hour, minute, second, and microsecond of the current date and time with zeros.
- `obj.get`: used to access the "ts" key in an event dictionary.
- `parent.exists`: used to check if the parent directory of the audit log file exists.
- `parent.glob`: used to find archived log files in the parent directory.
- `path.exists`: used to check if the audit log file exists.
- `pathlib.Path`: used to create a Path object for the audit log file.
- `since.isoformat`: used to convert the `since` timestamp to an ISO-formatted string.
- `vivarium.scout.audit.AuditLog`: used to create an AuditLog object for the current audit log file.

## Potential Considerations
The code handles the following edge cases and potential considerations:
- If the provided `period` is not one of the expected values, it defaults to a period of one day.
- If the audit log file does not exist, it skips loading events from it.
- If an archived log file does not have a valid timestamp in its name, it skips loading events from it.
- If a line in an archived log file is not valid JSON, it skips loading the event.
- The function uses a try-finally block to ensure that the current audit log file is closed after querying it, regardless of whether an exception occurs.
- The function sorts the events by their timestamp before returning them, which may impact performance for large numbers of events.

## Signature
The function signature is:
```python
def load_audit_log(period: str, audit_path: Optional[Path] = None) -> List[Dict[str, Any]]:
```
This indicates that the function:
- Takes two parameters: `period` (a string) and `audit_path` (an optional Path object).
- Returns a list of dictionaries, where each dictionary represents an audit event.
- The `audit_path` parameter has a default value of `None`, which means that the function will use a default audit log path if no value is provided.
---

# calculate_accuracy

## Logic Overview
The `calculate_accuracy` function computes accuracy metrics based on a list of events. The main steps are:
1. Filtering the events into two categories: navigation events (`nav_events`) and validation failure events (`validation_fails`).
2. Calculating the total number of navigation events (`total_nav`) and the number of validation failures (`fail_count`).
3. If there are no navigation events, the function returns a dictionary with `total_nav` as 0, `validation_fail_count` as the number of validation failures, and `accuracy_pct` as 100.0.
4. Otherwise, it calculates the accuracy as a percentage by subtracting the number of validation failures from the total number of navigation events, dividing by the total number of navigation events, and multiplying by 100.0.
5. The function returns a dictionary containing the total number of navigation events, the number of validation failures, and the calculated accuracy percentage, rounded to two decimal places.

## Dependency Interactions
The function uses the following traced calls:
- `e.get`: This is used to access the value of a key in a dictionary. Specifically, it is used to check the value of the `"event"` key in each event dictionary.
- `len`: This is used to get the number of elements in a list. It is used to calculate the total number of navigation events (`total_nav`) and the number of validation failures (`fail_count`).
- `round`: This is used to round the calculated accuracy to two decimal places.

## Potential Considerations
- Edge case: If the input list of events is empty, the function will not throw an error but will return a dictionary with default values.
- Error handling: The function does not have explicit error handling. If the input is not a list of dictionaries or if the dictionaries do not contain the expected keys, the function may throw an error.
- Performance: The function has a time complexity of O(n), where n is the number of events, because it iterates over the list of events twice. This should be efficient for most use cases, but it could be a consideration for very large lists of events.

## Signature
The function signature is `def calculate_accuracy(events: List[Dict[str, Any]]) -> Dict[str, Any]`. This indicates that:
- The function takes one argument, `events`, which is a list of dictionaries. Each dictionary can have any string key and any value.
- The function returns a dictionary with string keys and any values.
Note that the types `List` and `Dict` are not explicitly imported in the provided code, but they are commonly used in Python type hints to indicate lists and dictionaries, respectively. The `Any` type indicates that the values in the dictionaries can be of any type.
---

# generate_report

## Logic Overview
The `generate_report` function generates a report from audit events based on the provided period, compare model, and audit path. The main steps in the function are:
1. Loading audit events using `load_audit_log`.
2. Calculating scout cost by summing the costs of "nav" and "brief" events.
3. Determining the cost per navigation based on the compare model.
4. Calculating naive cost, savings, and savings percentage.
5. Calculating accuracy data using `calculate_accuracy`.
6. Calculating average navigation duration.
7. Returning a dictionary with the calculated report data.

## Dependency Interactions
The `generate_report` function interacts with the following traced calls:
* `load_audit_log`: Loads audit events based on the provided period and audit path.
* `MODEL_RATES.get`: Retrieves the cost per navigation for the compare model.
* `calculate_accuracy`: Calculates accuracy data from the audit events.
* `compare_model.lower`: Converts the compare model to lowercase for case-insensitive comparison.
* `e.get`: Retrieves values from audit event dictionaries.
* `len`: Calculates the number of navigation events.
* `max`: Ensures savings are not negative.
* `round`: Rounds savings percentage, accuracy percentage, and average navigation duration to one decimal place.
* `sum`: Calculates the total cost of "nav" and "brief" events and the total duration of navigation events.

## Potential Considerations
The code has the following potential considerations:
* Edge case: If there are no navigation events, `nav_count` will be zero, and `avg_nav_s` will be zero.
* Edge case: If `naive_cost` is zero, `savings_pct` will be 100.0.
* Error handling: The function does not handle errors that may occur when loading audit events or calculating accuracy data.
* Performance: The function iterates over the audit events multiple times, which may impact performance for large datasets.

## Signature
The `generate_report` function has the following signature:
```python
def generate_report(
    period: str,
    compare_model: Optional[str] = None,
    audit_path: Optional[Path] = None,
) -> Dict[str, Any]:
```
This signature indicates that the function:
* Takes three parameters: `period`, `compare_model`, and `audit_path`.
* `period` is a required string parameter.
* `compare_model` and `audit_path` are optional parameters with default values of `None`.
* Returns a dictionary with string keys and values of any type.
---

# _load_docs_for_file

## Logic Overview
The `_load_docs_for_file` function loads documentation files (.tldr.md and .deep.md) for a given file. The main steps are:
1. It checks for the existence of documentation files in the `.docs` directory relative to the file's parent directory.
2. If no documentation files are found, it attempts to find them in a central location (`docs/livingDoc/`) relative to the repository root.
3. It reads the contents of the found documentation files and joins them with a separator (`\n\n---\n\n`).
4. If no documentation files are found, it returns an empty string.

## Dependency Interactions
The function interacts with the following traced calls:
* `doc_path.exists()`: Checks if a documentation file exists.
* `doc_path.read_text()`: Reads the contents of a documentation file.
* `file_path.relative_to(repo_root)`: Gets the relative path of the file from the repository root.
* `parts.append()`: Adds the contents of a documentation file to a list of parts.

## Potential Considerations
The function handles the following edge cases and errors:
* If a documentation file does not exist, it skips to the next step.
* If reading a documentation file fails (e.g., due to an `OSError`), it skips that file.
* If the file is not within the repository root, it catches the `ValueError` exception and returns an empty string.
* The function uses `errors="replace"` when reading documentation files, which replaces unencodable characters with a replacement marker.

## Signature
The function signature is:
```python
def _load_docs_for_file(file_path: Path, repo_root: Path) -> str
```
It takes two parameters:
* `file_path`: The path to the file for which to load documentation.
* `repo_root`: The path to the repository root.
It returns a string containing the contents of the loaded documentation files, or an empty string if no documentation files are found.
---

# _run_roast

## Logic Overview
The `_run_roast` function is designed to run a Large Language Model (LLM) critique on a list of target files. The main steps of the function are:
1. Check if the `roast` configuration is enabled. If not, return a message indicating that roast is disabled.
2. Initialize an empty list `combined_docs` to store the documentation and code for each target file.
3. Iterate over each target file:
   - Check if the file exists and has a `.py` suffix. If not, skip to the next file.
   - Load the documentation for the file if `use_docs` is `True`.
   - Read the code from the file and create a block of text containing the file's relative path, documentation (if any), and code.
   - Append the block to `combined_docs`.
4. If `combined_docs` is empty, return a message indicating that there are no valid Python files to critique.
5. Create a prompt for the LLM by concatenating the blocks in `combined_docs` with a header asking the LLM to identify risks, anti-patterns, and improvements in the code.
6. Run the LLM using `asyncio.run` and `call_groq_async`, passing in the prompt and other parameters.
7. Log the result of the LLM critique using `AuditLog`.
8. Return the content of the LLM response.

## Dependency Interactions
The `_run_roast` function interacts with the following dependencies:
- `ScoutConfig`: used to get the `roast` configuration.
- `_load_docs_for_file`: used to load the documentation for each target file if `use_docs` is `True`.
- `asyncio.run`: used to run the LLM asynchronously.
- `call_groq_async`: used to call the LLM with the prompt and other parameters.
- `AuditLog`: used to log the result of the LLM critique.
- `Path`: used to represent file paths.
- `str`: used to represent strings, such as the prompt and the LLM response.
- `vivarium.scout.audit.AuditLog`: used to log the result of the LLM critique.
- `vivarium.scout.config.ScoutConfig`: used to get the `roast` configuration.
- `vivarium.scout.llm.call_groq_async`: used to call the LLM with the prompt and other parameters.

## Potential Considerations
The code handles the following potential considerations:
- **Error handling**: the function catches exceptions when reading files and running the LLM, and returns an error message if an exception occurs.
- **Performance**: the function reads the code from each file and creates a block of text containing the file's relative path, documentation (if any), and code. This could potentially be slow if the files are very large.
- **Edge cases**: the function checks if each file exists and has a `.py` suffix before attempting to read it. If a file does not exist or does not have a `.py` suffix, it is skipped.
- **Configuration**: the function checks the `roast` configuration to determine if the LLM critique should be run. If the `roast` configuration is not enabled, the function returns a message indicating that roast is disabled.

## Signature
The signature of the `_run_roast` function is:
```python
def _run_roast(target_files: List[Path], use_docs: bool, repo_root: Path) -> str
```
This indicates that the function takes three parameters:
- `target_files`: a list of `Path` objects representing the files to be critiqued.
- `use_docs`: a boolean indicating whether to use documentation when critiquing the files.
- `repo_root`: a `Path` object representing the root of the repository.
The function returns a string, which is the content of the LLM response.
---

# format_report

## Logic Overview
The `format_report` function is designed to format a roast report as an ASCII box. The main steps in the function are:
1. Initialization of the report's width and lines.
2. Construction of the report's header and body lines, including the period, scout spent, expensive model avoided, savings, accuracy, and average navigation time.
3. Conditional inclusion of a comparison model, if available.
4. Addition of a footer line to the report.
5. Joining of all lines with newline characters and returning the resulting string.

## Dependency Interactions
The function interacts with the following traced calls:
- `data.get`: This method is used to retrieve the value associated with the key `"compare_model"` from the `data` dictionary. If the key is not present, it returns `None` by default.
- `lines.append`: This method is used to add new lines to the `lines` list, which stores the individual lines of the report.

## Potential Considerations
Based on the code, the following potential considerations can be identified:
- **Error Handling**: The function does not include explicit error handling for cases such as missing or invalid data in the `data` dictionary. For example, if the `"period"` key is missing, a `KeyError` will be raised.
- **Edge Cases**: The function does not account for edge cases such as empty or `None` values in the `data` dictionary. For example, if the `"scout_cost"` value is `None`, a `TypeError` will be raised when attempting to format it as a float.
- **Performance**: The function uses string concatenation and formatting, which can be inefficient for large reports. However, given the fixed width and relatively small number of lines, performance is unlikely to be a significant concern.

## Signature
The function signature is:
```python
def format_report(data: Dict[str, Any]) -> str:
```
This indicates that the function:
- Takes a single argument `data`, which is a dictionary with string keys and values of any type.
- Returns a string value, which is the formatted report. 

Note that the function uses types from the `typing` module (e.g., `Dict`, `Any`), but these are not explicitly imported in the provided code snippet. The imports listed in the traced facts (e.g., `vivarium/scout/audit.py`, `vivarium/scout/config.py`, `vivarium/scout/llm.py`) do not appear to be directly related to the function's implementation.
---

# main

## Logic Overview — Flow and main steps from the code.
The `main` function is the entry point of the CLI application. It can be broken down into the following main steps:
1. **Argument Parsing**: The function initializes an `ArgumentParser` instance and defines several command-line arguments, including `--today`, `--week`, `--month`, `--target`, `--use-docs`, `--no-use-docs`, `--compare`, and `--audit-path`.
2. **Argument Validation**: After parsing the arguments, the function checks if a target file is provided. If a target file is provided, it runs the `_run_roast` function with the specified target files, use_docs flag, and repository root.
3. **Report Generation**: If no target file is provided, the function checks if a period (`--today`, `--week`, or `--month`) is specified. If not, it raises an error. Otherwise, it generates a report using the `generate_report` function with the specified period, compare model, and audit path.
4. **Report Formatting and Printing**: The generated report is then formatted using the `format_report` function and printed to the console.

## Dependency Interactions — How it uses the traced calls (reference qualified names).
The `main` function interacts with the following dependencies:
* `argparse.ArgumentParser`: used to create an argument parser instance.
* `argparse.ArgumentParser.add_argument`: used to add command-line arguments to the parser.
* `argparse.ArgumentParser.add_mutually_exclusive_group`: used to create a mutually exclusive group for the `--today`, `--week`, and `--month` arguments.
* `argparse.ArgumentParser.parse_args`: used to parse the command-line arguments.
* `argparse.ArgumentParser.error`: used to raise an error if the required arguments are not provided.
* `_run_roast`: used to run the roast function with the specified target files and flags.
* `generate_report`: used to generate a report with the specified period, compare model, and audit path.
* `format_report`: used to format the generated report.
* `pathlib.Path.cwd`: used to get the current working directory.
* `print`: used to print the result or the formatted report to the console.

## Potential Considerations — Edge cases, error handling, performance from the code.
The code handles the following edge cases and errors:
* If no target file is provided and no period is specified, it raises an error using `parser.error`.
* If a target file is provided, it runs the `_run_roast` function and prints the result.
* The `--use-docs` and `--no-use-docs` flags are used to control the inclusion of living docs in the critique.
* The `--compare` flag is used to specify a compare model for the report.
* The `--audit-path` flag is used to override the default audit log path.

## Signature — `def main() -> int`
The `main` function is defined with a return type of `int`, indicating that it returns an integer value. In this case, the function returns `0` to indicate successful execution.