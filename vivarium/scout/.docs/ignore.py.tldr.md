# BUILT_IN_IGNORES

**BUILT_IN_IGNORES**
================

The `BUILT_IN_IGNORES` constant is used to store a set of names that are ignored by the `inspect` module when searching for built-in modules. It is primarily used to exclude built-in modules from inspection.
---

# _glob_to_regex

Converts a glob pattern to a regex pattern, supporting '*' and '**' wildcards.
The function iterates over the pattern, replacing '*' with '.*' and '**' with '.*' recursively, to create a regex pattern that can be used for matching. 
It depends on the provided glob pattern string.
---

# _normalize_path

**Summary**

The `_normalize_path` function normalizes a given path for matching purposes. It resolves the `~` symbol and ensures the path uses forward slashes. The function takes a `path` and an optional `repo_root` as input, returning a normalized string representation of the path.
---

# IgnorePatterns

**IgnorePatterns Class Summary**
================================

The `IgnorePatterns` class is responsible for matching paths against built-in and user-defined ignore patterns. It supports globstar patterns (**), negation (!), and standard fnmatch patterns, allowing for flexible path matching. This class depends on user-defined patterns from a `.livingDocIgnore` file, similar to a gitignore file.
---

# __init__

The `__init__` method is a special Python method that initializes an object when it's created. Its primary purpose is to set up the object's attributes and perform any necessary setup or initialization. It takes two optional parameters, `repo_root` and `ignore_file`, which are used to configure the object's behavior.
---

# _load_patterns

The `_load_patterns` method loads built-in and user-defined patterns, iterating through them as needed, and handling any potential exceptions that may arise during the process. It is responsible for populating patterns for use in the application. This method depends on the presence of patterns to load.
---

# matches

**matches method summary**
==========================

The `matches` method determines whether a given path should be ignored during processing. It checks for built-in ignore rules, positive user-defined rules, and negative user-defined rules, with negation overriding other rules. The method returns `True` if the path should be ignored.
---

# reload

The `reload` method reloads patterns from disk, typically after editing `.livingDocIgnore` files. Its primary responsibility is to update the patterns in memory. It depends on the existence of `.livingDocIgnore` files and calls an unspecified function to achieve this.