# logger

The `logger` constant is not explicitly documented, but based on its interactions, it appears to be a logging utility used for outputting messages or errors in the vivarium/scout project. Its primary purpose is to handle logging functionality, and it likely interacts with the dependencies listed to configure or utilize logging features.
---

# TLDR_MODEL

The `TLDR_MODEL` constant is not explicitly documented, but based on its interactions, it appears to be a model or configuration related to the TLDR (Too Long; Didn't Read) feature in the Vivarium Scout. 

It likely depends on the LLM (Large Language Model) configuration from `vivarium/scout/llm.py` and possibly uses or is influenced by configurations from `vivarium/scout/config.py`.
---

# DEEP_MODEL

The Python constant 'DEEP_MODEL' is not explicitly documented, but based on its interactions with other modules, it appears to be a configuration constant related to deep learning models. 

It likely controls or references a specific deep learning model used in the vivarium/scout/llm.py module, possibly influencing the behavior of the scout.
---

# ELIV_MODEL

The Python constant 'ELIV_MODEL' is not explicitly defined in the provided information. However, based on the dependencies, it is likely related to the LLM (Large Language Model) functionality in the vivarium/scout/llm.py module. 

It may be used to store or reference a specific LLM model, possibly for use in the vivarium/scout/audit.py, vivarium/scout/config.py, or vivarium/scout/ignore.py modules.
---

# _extract_logic_hints

**Function Summary: `_extract_logic_hints`**

The `_extract_logic_hints` function extracts logic hints from a function or method body by scanning Abstract Syntax Tree (AST) nodes. It identifies and returns hints related to loops, returns, function calls, and conditional statements. This function relies on dependencies from the vivarium/scout module, specifically `vivarium/scout/audit.py`, `vivarium/scout/config.py`, `vivarium/scout/ignore.py`, and `vivarium/scout/llm.py`.
---

# _build_signature

**_build_signature Function Summary**
=====================================

The `_build_signature` function builds a signature string for a function or async function, considering exception handling, loops, returns, conditionals, and calls. It takes an abstract syntax tree (AST) node as input and returns a string representation of the function's signature. The function interacts with dependencies from the `vivarium/scout` package, specifically `audit.py`, `config.py`, `ignore.py`, and `llm.py`.
---

# _parse_assign_targets

**_parse_assign_targets Function Summary**

The `_parse_assign_targets` function extracts names from an assignment target, handling tuple unpacking. It iterates over the assignment node, returning a list of extracted names. This function depends on the `vivarium/scout` package, specifically interacting with `audit.py`, `config.py`, `ignore.py`, and `llm.py`.
---

# parse_python_file

**parse_python_file Function Summary**
=====================================

The `parse_python_file` function parses a Python file using the Abstract Syntax Tree (AST) to extract top-level symbols, including classes, functions, methods, and constants. It captures symbol metadata such as name, type, line range, docstring, and logic hints. The function relies on dependencies from the vivarium/scout package for configuration and logic hint analysis.
---

# extract_source_snippet

**extract_source_snippet Function Summary**
=============================================

The `extract_source_snippet` function reads a specific Python file and returns the raw source code lines between `start_line` and `end_line` inclusive. It relies on accurate line numbers from `parse_python_file` and handles exceptions for file existence, readability, and decoding.
---

# _build_tldr_prompt

**_build_tldr_prompt Function Summary**

The `_build_tldr_prompt` function builds a Large Language Model (LLM) prompt for generating a TL;DR summary. It takes in `symbol_info` and `dependencies` as inputs and returns a string prompt. The function depends on various modules from the vivarium/scout package, including `audit.py`, `config.py`, `ignore.py`, and `llm.py`, to construct the prompt based on the provided information.
---

# _generate_tldr_async

Async implementation of TL;DR generation, returning an error string on non-RuntimeError failures. It calls other functions from dependencies to generate a TL;DR, handling exceptions and returning the result as a string. The function relies on the `vivarium/scout` package for configuration, audit, and ignore logic.
---

# generate_tldr_content

**TL;DR Summary**
Generate a concise, high-level summary of a single symbol using a Large Language Model (LLM). The summary explains the primary purpose and key responsibilities of the symbol, and briefly describes its relationship with dependencies.
---

# _build_deep_prompt

**_build_deep_prompt Function Summary**
=====================================

The `_build_deep_prompt` function builds a Large Language Model (LLM) prompt for deep content generation. It takes in symbol information, dependencies, and a source code snippet, and returns a formatted string. The function relies on various dependencies, including `vivarium/scout/audit.py`, `vivarium/scout/config.py`, `vivarium/scout/ignore.py`, and `vivarium/scout/llm.py`, to construct the prompt.
---

# _generate_deep_content_async

Async implementation of deep content generation, responsible for generating content based on provided symbol information, dependencies, and source code snippet. It returns an error string on non-RuntimeError failures. It interacts with various scout modules for configuration, audit, and LLM (Large Language Model) functionality.
---

# generate_deep_content

**generate_deep_content Function Summary**

The `generate_deep_content` function generates a detailed breakdown of a single symbol using a Large Language Model (LLM). It takes in symbol information, dependencies, and source code snippet, and returns the LLM-generated Markdown content as a string. This function relies on the `vivarium/scout/llm.py` module to interact with the LLM and logs the cost to the Scout audit trail.
---

# _build_eliv_prompt

**_build_eliv_prompt Function Summary**

The `_build_eliv_prompt` function builds the LLM (Large Language Model) prompt for ELIV (Explain Like I'm Very Young) generation. It takes in symbol information, dependencies, and a source code snippet, and returns a formatted string. The function relies on various dependencies from the vivarium/scout module to construct the prompt.
---

# _generate_eliv_async

Async implementation of ELIV generation, responsible for generating ELIV asynchronously based on provided symbol information, dependencies, and source code snippet. It handles exceptions and returns an error string on non-RuntimeError failures. It interacts with various scout modules for configuration, audit, and LLM functionality.
---

# generate_eliv_content

**generate_eliv_content Function Summary**

The `generate_eliv_content` function generates a simplified "Explain Like I'm Very Young" (ELIV) explanation for a code symbol, using Groq's LLM to produce a beginner-friendly explanation based on the symbol's information, dependencies, and source code. It logs the cost to the Scout audit trail and raises a `RuntimeError` if the GROQ_API_KEY is not set.
---

# validate_generated_docs

**validate_generated_docs Function Summary**
=============================================

The `validate_generated_docs` function validates generated documentation content for a symbol, returning a boolean indicating validity and a list of error messages. It relies on external dependencies for configuration and logic, such as `vivarium/scout/audit.py` and `vivarium/scout/llm.py`.
---

# write_documentation_files

**write_documentation_files Function Summary**

The `write_documentation_files` function generates documentation files for a Python file. It writes three files: a brief summary (`<stem>.tldr.md`), a detailed description (`<stem>.deep.md`), and an ELIV file (`<name>.eliv.md`). The function depends on `vivarium/scout/audit.py`, `vivarium/scout/config.py`, `vivarium/scout/ignore.py`, and `vivarium/scout/llm.py` for configuration and functionality.
---

# _generate_single_symbol_docs

**Summary**

The `_generate_single_symbol_docs` function generates documentation for a single symbol, including TL;DR, deep, and ELIV content, while respecting a per-file semaphore to avoid event loop conflicts. It uses sync wrappers to process multiple files concurrently. The function depends on various modules from the `vivarium/scout` package to retrieve symbol information and perform language model-based processing.
---

# process_single_file_async

**process_single_file_async Summary**

The `process_single_file_async` function processes a single Python file for documentation generation, parsing the file, generating TL;DR and deep content for each symbol via LLM, and writing `.tldr.md` and `.deep.md` files. It concurrently handles symbol generations and validates the output. The function depends on `vivarium/scout/*` modules for configuration, dependency resolution, and LLM interactions.
---

# process_single_file

**process_single_file Function Summary**

The `process_single_file` function processes a single Python file for documentation generation, parsing the file, generating TL;DR and deep content for each symbol via a Large Language Model (LLM), and writing `.tldr.md` and `.deep.md` files.

Its primary responsibilities include:

* Parsing the file
* Generating documentation content via LLM
* Validating and aggregating content
* Writing output files

It depends on the `vivarium/scout` package, specifically `audit.py`, `config.py`, `ignore.py`, and `llm.py`, for functionality and configuration.
---

# _update_module_brief

**Function Summary: `_update_module_brief`**

The `_update_module_brief` function generates a module-level brief from package content by summarizing `.tldr.md` and `.deep.md` files using a Large Language Model (LLM). It writes the brief to two locations and logs an audit event, respecting configuration settings and ignoring certain patterns.
---

# process_directory

**Summary**

The `process_directory` function processes a directory of Python files for documentation generation. It recursively traverses the directory, generates module briefs, and writes generated docs to a specified output directory. It relies on external dependencies from `vivarium/scout/*` for configuration, auditing, and language model interactions.