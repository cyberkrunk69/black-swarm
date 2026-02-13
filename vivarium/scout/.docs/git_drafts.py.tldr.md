# _stem_for_file

**Summary**

The `_stem_for_file` function returns the stem (filename without extension) for a given file path relative to a specified repository root. It takes two parameters: `file_path` and `root`, both of which are file paths. The function is responsible for handling exceptions and returning the stem.
---

# assemble_pr_description

**assemble_pr_description Function Summary**

Assembles a PR description from draft files for each staged Python file in a repository. It reads draft files from `docs/drafts/{stem}.pr.md` or `docs/drafts/{stem}.pr.txt` for each staged `.py` file, and returns an aggregated Markdown string. The function iterates over staged files, handles conditional file existence, and falls back to a default message if no draft is found.
---

# assemble_commit_message

**assemble_commit_message Function Summary**
=============================================

Assembles a single commit message from draft files for each staged Python file.

**Primary Purpose:** 
The function aggregates commit messages from draft files for staged Python files.

**Key Responsibilities:**

* Reads draft files for each staged Python file
* Falls back to a default message if a draft file is missing
* Combines messages into a single aggregated string

**Relationship with Dependencies:**
The function depends on the `repo_root` and `staged_files` inputs, and returns a string output.