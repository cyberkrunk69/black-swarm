# BUILT_IN_IGNORES

`BUILT_IN_IGNORES` is a constant in Python's `inspect` module. It contains a list of names that are ignored when inspecting built-in modules. This constant is used to filter out built-in modules and their contents from the inspection process.
---

# _glob_to_regex

Converts a glob pattern to a regular expression, supporting both `*` and `**` wildcards.
The function iterates over the pattern, replacing `*` with `.*` and `**` with `.*` recursively, to create a regex pattern.
It depends on the provided glob pattern string and returns the corresponding regex pattern string.
---

# _normalize_path

**_normalize_path Function Summary**
=====================================

The `_normalize_path` function normalizes a given path for matching purposes, converting it to use forward slashes and resolving any `~` references. It takes a `path` and an optional `repo_root` as input, returning a normalized string representation of the path. This function depends on the `Path` and `Optional` types from the `pathlib` library.
---

# IgnorePatterns

**IgnorePatterns Class Summary**
================================

The `IgnorePatterns` class is responsible for matching paths against built-in and user-defined ignore patterns. It supports globstar patterns (**), negation (!), and standard fnmatch patterns, allowing for flexible path matching. This class depends on user-defined patterns from `.livingDocIgnore` files, similar to Gitignore files.
---

# __init__

The `__init__` method is a special Python method that initializes an object when it's created. Its primary purpose is to set up the object's attributes and perform any necessary setup or initialization. It takes two optional parameters, `repo_root` and `ignore_file`, which are used to configure the object's behavior.
---

# _load_patterns

The `_load_patterns` method loads built-in and user-defined patterns, iterating through them as needed, and handling any exceptions that may arise during the process. Its primary responsibility is to populate patterns for use in the application. It depends on no specific interactions or dependencies.
---

# matches

**matches method summary**
==========================

The `matches` method determines whether a given path should be ignored during processing. It checks for built-in ignore rules, positive user-defined rules, and negative user-defined rules, with negation taking precedence. The method returns `True` if the path should be ignored.
---

# reload

The `reload` method reloads patterns from disk, typically after editing `.livingDocIgnore` files. It is responsible for updating the patterns in memory to reflect the changes made on disk. This method depends on the presence of `.livingDocIgnore` files and the ability to read from disk.