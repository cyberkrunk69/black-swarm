# logger

The logger constant is not explicitly described in the provided information. However, based on the import statement, it is likely related to logging functionality. 

It imports from vivarium/scout/adapters/base.py, suggesting it may be used in an adapter or a base class for logging purposes.
---

# _BUILTIN_NAMES

The _BUILTIN_NAMES constant is used in the vivarium/scout/adapters/base.py module. It does not export any values or make any qualified calls.
---

# _build_import_map

The function _build_import_map iterates over the child nodes of an Abstract Syntax Tree (AST) module and checks if each node is an import statement. 

It appears to be responsible for building an import map from the AST of a Python module, likely for use in a static analysis or code generation context.
---

# _qualify_call_name

This function appears to be part of a system that processes or analyzes Python code. It calls the `isinstance` and `len` functions, suggesting it checks the type or length of an object. It also inserts elements into a list called `parts`, likely modifying the object being processed.
---

# _extract_calls_from_body

This function appears to extract calls from the body of an abstract syntax tree (AST) node. It iterates over child nodes, checks their types, and adds qualified call names to a list. The function uses a set to keep track of seen nodes to avoid duplicates.
---

# _extract_types_from_node

The function _extract_types_from_node extracts type information from a node in an Abstract Syntax Tree (AST) and appends it to a list. It checks if the node is an instance of ast.AST and uses the _name_from_annotation function to process annotation information.
---

# _extract_module_exports

The function _extract_module_exports iterates over the child nodes of an AST (Abstract Syntax Tree) module, filtering nodes with names starting with 'exports'. It appends these nodes to a list.

TL;DR: This function extracts export nodes from an AST module, likely for processing or analysis purposes. It iterates over the module's child nodes, filtering those with 'exports' in their names.
---

# _extract_logic_hints

This function walks an Abstract Syntax Tree (AST) and appends logic hints to a list. It checks the type of each node in the AST and uses string type.
---

# _build_signature

The function _build_signature appears to be responsible for parsing and manipulating Python function definitions, specifically handling asynchronous and synchronous functions. It utilizes the Abstract Syntax Trees (AST) to analyze and transform function signatures.
---

# _parse_assign_targets

The _parse_assign_targets function appears to be part of a larger system for parsing or analyzing Python code. It checks if an object is an instance of ast.Assign and appends names to a list.
---

# _is_simple_symbol

The function `_is_simple_symbol` checks if a `SymbolTree` is simple, likely using the `any` function and possibly attribute access via `getattr`. It does not export any values and is not directly related to the `base.py` module.
---

# _extract_return_expr

The _extract_return_expr function appears to be part of a system that works with Abstract Syntax Trees (ASTs). It uses the AST library to parse, walk, and unparse expressions, and it checks the type of an object using isinstance. The function likely extracts return expressions from a given code snippet.
---

# try_auto_tldr

This function appears to be part of a larger system for parsing or analyzing code, specifically working with SymbolTrees. It calls _extract_return_expr and _is_simple_symbol, suggesting it is involved in expression analysis or simplification.
---

# PythonAdapter

This Python class, PythonAdapter, appears to be a language adapter for processing Python code. It likely parses and analyzes Python files to extract information, such as function signatures, types, and logic hints, and stores this information in a SymbolTree data structure. It may also handle errors and exceptions related to file I/O and syntax.
---

# extensions

Simple extensions utility.
---

# parse

This method appears to be responsible for parsing a file, likely a Python script, and extracting its contents into a SymbolTree data structure. It handles various exceptions and errors that may occur during the parsing process, such as file not found or syntax errors.
---

# try_auto_tldr

This function appears to be part of a larger system for parsing or analyzing code, specifically working with SymbolTrees. It calls _extract_return_expr and _is_simple_symbol, suggesting it is involved in expression analysis or simplification.
---

# get_tldr_prompt

This method retrieves a prompt from a SymbolTree using the getattr function, likely to access a specific attribute or value. It returns a string prompt.
---

# get_deep_prompt

The `get_deep_prompt` method retrieves a deep prompt from a `SymbolTree` using `getattr` to access attributes. It takes three string arguments and returns a string.
---

# get_eliv_prompt

This method retrieves an attribute from an object of type SymbolTree using the getattr function. It takes three string arguments and returns no value.
---

# symbol_to_dict

The `symbol_to_dict` function is part of the `vivarium/scout/adapters/base.py` module. It appears to be a utility function that converts a `SymbolTree` object into a dictionary.