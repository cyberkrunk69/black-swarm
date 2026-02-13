# BUILT_IN_IGNORES

This constant is not used in the system as there are no traced calls or type usage.
---

# _glob_to_regex

This function takes a string as input, processes it, and appends the result to a list. It uses string manipulation and regular expression functionality. 

It appears to be a utility function that converts a glob pattern to a regular expression, possibly for use in a larger pattern matching system.
---

# _normalize_path

This function normalizes a path by expanding user directories and converting it to an absolute path. It uses the `pathlib` library to manipulate paths.
---

# IgnorePatterns

This class, IgnorePatterns, appears to manage ignore patterns for a file system. It loads patterns from a file, compiles them into regular expressions, and stores them in separate lists for positive and negative matches. It also provides methods to clear and append to these lists.
---

# __init__

This method initializes the object and loads patterns from the current working directory. It uses the `pathlib` library to interact with file paths. The method does not export any values or modify external state.
---

# _load_patterns

This method loads patterns from a file, likely a configuration file in the user's home directory, and populates lists of positive and negative patterns. It appears to handle built-in patterns and ignore files.
---

# matches

This method appears to normalize a file path and search for a pattern within it. It utilizes the `_normalize_path` function and the `pat.search` method to achieve this. The method operates on file paths and returns a boolean value.
---

# reload

The `reload` method appears to be responsible for reloading patterns, as it calls `self._load_patterns`. Its primary function is to update or refresh the patterns in the system.