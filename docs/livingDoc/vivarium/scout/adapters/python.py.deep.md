# logger

## Logic Overview
The code defines a constant `logger` by calling the `getLogger` function from the `logging` module, passing `__name__` as an argument. This suggests that the logger is being configured to log events related to the current module.

## Dependency Interactions
The code uses the `logging` module, but the traced facts do not show any direct calls to `logging` functions. However, it does import `vivarium/scout/adapters/base.py`, which may contain related functionality. The `logger` constant is defined using the `logging.getLogger` function, but no qualified name is used, implying that `logging` is imported directly.

## Potential Considerations
The code does not show any error handling or edge cases. The performance of the logger is not explicitly addressed in the code. The fact that no calls are traced suggests that the logger may not be used extensively in the provided code snippet.

## Signature
N/A
---

# _BUILTIN_NAMES

## Logic Overview
The code defines a constant `_BUILTIN_NAMES` as a `frozenset` of names from the `builtins` module. The main steps are:
1. It uses a generator expression to iterate over the names in the `builtins` module, obtained through the `dir()` function.
2. It filters out names that start with an underscore (`_`) using the `startswith()` method.
3. The resulting names are collected into a `frozenset`, which is an immutable set.

## Dependency Interactions
The code uses the following qualified names:
- `builtins`: The `builtins` module is used to get the list of built-in names.
- `dir()`: The `dir()` function is used to get the list of names in the `builtins` module.
- `frozenset`: The `frozenset` type is used to create an immutable set of names.

## Potential Considerations
- **Edge cases**: The code assumes that the `builtins` module is available and can be iterated over using `dir()`. If this is not the case, the code may fail.
- **Error handling**: The code does not include any explicit error handling. If an error occurs while executing the code (e.g., if `builtins` is not available), it will propagate up the call stack.
- **Performance**: The code uses a generator expression, which can be more memory-efficient than creating a list of names. However, the performance impact is likely to be small unless the `builtins` module is very large.

## Signature
N/A
---

# _build_import_map

## Logic Overview
The `_build_import_map` function takes an `ast.Module` object as input and returns a dictionary mapping local names to fully qualified module symbols for imports. The main steps in the function are:
1. Initialize an empty dictionary `import_map`.
2. Iterate over all child nodes of the input `tree` using `ast.iter_child_nodes`.
3. For each node, check if it's an `ast.Import` or `ast.ImportFrom` node.
   - If it's an `ast.Import` node, iterate over its `names` attribute and add each alias to the `import_map`.
   - If it's an `ast.ImportFrom` node, iterate over its `names` attribute and add each alias to the `import_map` with the module name as a prefix.
4. Return the populated `import_map`.

## Dependency Interactions
The function uses the following traced calls:
- `ast.iter_child_nodes(tree)`: This call is used to iterate over all child nodes of the input `tree`.
- `isinstance(node, ast.Import)` and `isinstance(node, ast.ImportFrom)`: These calls are used to check the type of each node.
The function also uses types from the `ast` module, specifically `ast.Module`, `ast.Import`, and `ast.ImportFrom`.

## Potential Considerations
Based on the code, the following potential considerations can be identified:
- The function does not handle any potential errors that may occur during the iteration over the child nodes or the construction of the `import_map`.
- The function assumes that the input `tree` is a valid `ast.Module` object and does not perform any validation checks.
- The function uses a simple dictionary to store the import map, which may lead to performance issues for large input trees.
- The function does not handle the case where a local name is imported multiple times with different fully qualified module symbols.

## Signature
The function signature is `def _build_import_map(tree: ast.Module) -> Dict[str, str]`. This indicates that:
- The function takes a single argument `tree` of type `ast.Module`.
- The function returns a dictionary with string keys and string values.
- The function is intended to be used internally (as indicated by the leading underscore in its name) to build a map of local names to fully qualified module symbols for imports.
---

# _qualify_call_name

## Logic Overview
The `_qualify_call_name` function takes in three parameters: `node` of type `ast.Call`, `import_map` of type `Dict[str, str]`, and `local_scope` of type `Set[str]`. It aims to resolve a call to a qualified name (module.path.func) when possible. The main steps are:
1. Extracting the function (`func`) from the input `node`.
2. Iterating through the function's attributes to construct a list of parts (`parts`) that form the qualified name.
3. Checking if the current expression (`cur`) is an instance of `ast.Name` and adding its id to the `parts` list if so.
4. Joining the `parts` list into a string (`name`) with '.' as the separator.
5. Checking the length of `parts` and its presence in `import_map` to determine the final qualified name.

## Dependency Interactions
The function interacts with the following traced calls:
- `isinstance`: used to check if the current expression (`cur`) is an instance of `ast.Attribute` or `ast.Name`.
- `len`: used to check the length of the `parts` list.
- `parts.insert`: used to add elements to the `parts` list.
These interactions are crucial for constructing the qualified name and handling different types of function calls.

## Potential Considerations
Based on the code, the following potential considerations can be identified:
- Edge cases: The function returns `None` if the current expression is not an instance of `ast.Name`, which might occur in cases like lambda functions.
- Error handling: The function does not explicitly handle errors, but it returns `None` in certain cases, which might be considered as a form of error handling.
- Performance: The function's performance is likely to be efficient since it only involves iterating through the function's attributes and checking the presence of elements in the `import_map`.

## Signature
The function signature is:
```python
def _qualify_call_name(node: ast.Call, import_map: Dict[str, str], local_scope: Set[str]) -> str | None
```
This signature indicates that the function:
- Takes in three parameters: `node`, `import_map`, and `local_scope`.
- Returns either a string (`str`) or `None`.
- Uses type hints to specify the expected types of the parameters and return value.
Note that the `local_scope` parameter is not used within the function, which might be an indication of a potential issue or a future development.
---

# _extract_calls_from_body

## Logic Overview
The `_extract_calls_from_body` function is designed to extract qualified call names from a given function or class body. The main steps involved in this process are:
1. Initialization of an empty list `calls` to store the extracted call names and an empty set `seen` to keep track of unique call names.
2. Definition of a nested function `visit` that recursively traverses the abstract syntax tree (AST) of the given body.
3. The `visit` function checks if a node is a call (i.e., an instance of `ast.Call`) and if so, it qualifies the call name using the `_qualify_call_name` function.
4. If the qualified call name is not empty and has not been seen before, it is added to the `seen` set and appended to the `calls` list.
5. The `visit` function is applied to each statement in the given body.
6. Finally, the function returns the sorted list of extracted call names.

## Dependency Interactions
The `_extract_calls_from_body` function interacts with the following traced calls:
* `_qualify_call_name`: This function is called to qualify the name of a call node in the AST. It takes the call node, `import_map`, and `local_scope` as arguments.
* `ast.iter_child_nodes`: This function is used to iterate over the child nodes of a given node in the AST.
* `calls.append`: This method is used to add a qualified call name to the `calls` list.
* `isinstance`: This function is used to check if a node is an instance of `ast.Call`.
* `seen.add`: This method is used to add a qualified call name to the `seen` set.
* `set`: This type is used to create an empty set `seen` to keep track of unique call names.
* `sorted`: This function is used to sort the list of extracted call names before returning it.
* `visit`: This is a nested function defined within `_extract_calls_from_body` that recursively traverses the AST and extracts call names.

## Potential Considerations
Based on the code, some potential considerations include:
* Error handling: The function does not seem to handle any potential errors that may occur during the extraction process, such as invalid AST nodes or missing import maps.
* Performance: The function uses a recursive approach to traverse the AST, which may lead to performance issues for large bodies of code.
* Edge cases: The function assumes that the input body is a list of AST nodes, but it does not check for invalid or empty inputs.

## Signature
The signature of the `_extract_calls_from_body` function is:
```python
def _extract_calls_from_body(
    body: list,
    import_map: Dict[str, str],
    local_scope: Set[str],
) -> List[str]:
```
This signature indicates that the function takes three arguments:
* `body`: a list of AST nodes representing the function or class body.
* `import_map`: a dictionary mapping import names to their corresponding qualified names.
* `local_scope`: a set of local variable names.
The function returns a list of extracted call names. The types of the arguments and return value are specified using type hints.
---

# _extract_types_from_node

## Logic Overview
The `_extract_types_from_node` function is designed to extract type names from annotations in an Abstract Syntax Tree (AST) node. The main steps are:
1. Initialize an empty list `types` to store the extracted type names.
2. Define a nested function `_name_from_annotation` to extract the type name from an annotation.
3. Check the type of the input `node` and extract type names accordingly:
   - For function definitions (`ast.FunctionDef` or `ast.AsyncFunctionDef`), extract type names from argument annotations and the return annotation.
   - For annotated assignments (`ast.AnnAssign`), extract the type name from the annotation.
   - For class definitions (`ast.ClassDef`), extract type names from the base classes.
4. Return the list of extracted type names.

## Dependency Interactions
The function uses the following traced calls:
- `_name_from_annotation(ann: ast.expr | None)`: This is a nested function that takes an annotation expression and returns the type name as a string or `None`.
- `isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))`: This checks if the input `node` is a function definition or an asynchronous function definition.
- `isinstance(ann, ast.Name)`, `isinstance(ann, ast.Attribute)`, `isinstance(ann, ast.Subscript)`, `isinstance(ann, ast.BinOp)`: These check the type of the annotation expression in the `_name_from_annotation` function.
- `types.append(t)`: This adds the extracted type name to the `types` list.

## Potential Considerations
- Edge cases: The function does not handle all possible types of annotations (e.g., `ast.Call`, `ast.List`, etc.). It may not work correctly for complex annotations.
- Error handling: The function does not handle any errors that may occur during the extraction process. For example, if the input `node` is not a valid AST node, the function may raise an exception.
- Performance: The function uses recursive calls to extract type names from annotations. This may lead to performance issues for large AST nodes.

## Signature
The function signature is:
```python
def _extract_types_from_node(node: ast.AST) -> List[str]
```
This indicates that the function takes an `ast.AST` node as input and returns a list of strings representing the extracted type names. The function is prefixed with an underscore, suggesting that it is intended to be a private function within a module.
---

# _extract_module_exports

## Logic Overview
The `_extract_module_exports` function takes an `ast.Module` object as input and returns a list of strings representing the exports of the module. The function iterates over the child nodes of the input module. It checks for two types of nodes:
- `ast.Assign` nodes, specifically those that assign a value to the `__all__` variable. If such a node is found, it extracts the values from the assigned list or tuple and adds them to the `exports` list.
- `ast.FunctionDef`, `ast.AsyncFunctionDef`, and `ast.ClassDef` nodes, which represent function and class definitions. If a node of one of these types is found and its name does not start with an underscore, its name is added to the `exports` list.

## Dependency Interactions
The function uses the following traced calls:
- `ast.iter_child_nodes(tree)`: This call is used to iterate over the child nodes of the input `ast.Module` object.
- `exports.append(...)`: This call is used to add export names to the `exports` list.
- `isinstance(...)`: This call is used to check the type of nodes and values, such as `ast.Assign`, `ast.Name`, `ast.List`, `ast.Tuple`, `ast.Str`, `ast.Constant`, `ast.FunctionDef`, `ast.AsyncFunctionDef`, and `ast.ClassDef`.
- `node.name.startswith("_")`: This call is used to check if a node's name starts with an underscore.

## Potential Considerations
The function does not handle potential errors that may occur during execution, such as:
- If the input `tree` is not a valid `ast.Module` object.
- If the `__all__` variable is assigned a value that is not a list or tuple.
- If the list or tuple assigned to `__all__` contains values that are not strings.
- The function returns an empty list if no exports are found, but it does not raise an error or provide any indication that no exports were found.

The function also does not consider performance implications, such as:
- The function iterates over all child nodes of the input module, which could be time-consuming for large modules.
- The function uses the `isinstance` function to check the type of nodes and values, which could be slower than using other methods to check types.

## Signature
The function signature is `def _extract_module_exports(tree: ast.Module) -> List[str]`. This indicates that:
- The function takes a single argument `tree` of type `ast.Module`.
- The function returns a list of strings.
- The function is intended to be private (due to the leading underscore in its name), suggesting that it should not be called directly from outside the module where it is defined.
---

# _extract_logic_hints

## Logic Overview
The `_extract_logic_hints` function takes an Abstract Syntax Tree (AST) node representing a function or method definition and extracts logic hints from its body. The main steps are:
1. Initialize an empty list `hints` to store the extracted logic hints.
2. Iterate over all child nodes of the input `node` using `ast.walk`.
3. For each child node, check its type and append a corresponding hint to the `hints` list if it's not already present.
4. Return the `hints` list containing the extracted logic hints.

## Dependency Interactions
The function interacts with the following dependencies:
* `ast.walk`: This function is used to iterate over all child nodes of the input `node`. The qualified name is `ast.walk`.
* `hints.append`: This method is used to add a new hint to the `hints` list. The qualified name is `list.append`.
* `isinstance`: This function is used to check the type of each child node. The qualified name is `builtins.isinstance`.
* `vivarium/scout/adapters/base.py`: This import is not directly used in the function, but it might be related to the context in which the function is used.

## Potential Considerations
Based on the code, the following potential considerations can be identified:
* Edge cases: The function does not handle any potential errors that might occur during the iteration over the child nodes or the type checking. It assumes that the input `node` is a valid AST node.
* Error handling: The function does not have any explicit error handling mechanisms. If an error occurs, it will be propagated to the caller.
* Performance: The function uses `ast.walk` to iterate over all child nodes, which might be inefficient for large ASTs. However, this is a necessary step to extract the logic hints.

## Signature
The function signature is:
```python
def _extract_logic_hints(node: ast.FunctionDef | ast.AsyncFunctionDef) -> List[str]:
```
This indicates that the function:
* Takes a single argument `node` which can be either an `ast.FunctionDef` or an `ast.AsyncFunctionDef`.
* Returns a list of strings (`List[str]`) containing the extracted logic hints.
* The function name starts with an underscore, indicating that it's intended to be a private function.
---

# _build_signature

## Logic Overview
The `_build_signature` function takes a node of type `ast.FunctionDef` or `ast.AsyncFunctionDef` as input and returns a string representing the function signature. The main steps in the function are:
1. Attempt to create a new function definition node (`sig_node`) with the same name, arguments, and return type as the input node, but with an empty body.
2. If the input node is an `ast.AsyncFunctionDef`, create an `ast.AsyncFunctionDef` node; otherwise, create an `ast.FunctionDef` node.
3. Copy the location of the input node to the new node using `ast.copy_location`.
4. Unparse the new node into a string using `ast.unparse`.
5. Extract the function signature from the unparsed string by finding the index of the first colon and newline characters (`:\n`).
6. If the index is not found, remove the `: pass` statement and trailing whitespace from the unparsed string.
7. If an exception occurs during the above steps, the function falls back to a simpler approach:
   - Determine the prefix of the function signature based on whether the input node is an `ast.AsyncFunctionDef` or `ast.FunctionDef`.
   - Iterate over the arguments of the input node, excluding `self` and `cls`, and append their names to a list.
   - Iterate over the default values of the input node, and update the corresponding argument names in the list to include the default value.
   - Construct the function signature by concatenating the prefix, function name, and argument list.

## Dependency Interactions
The `_build_signature` function interacts with the following traced calls:
- `ast.AsyncFunctionDef`: Creates a new asynchronous function definition node.
- `ast.FunctionDef`: Creates a new function definition node.
- `ast.Pass`: Creates a pass statement node, used as the body of the new function definition node.
- `ast.copy_location`: Copies the location of the input node to the new node.
- `ast.unparse`: Unparses the new node into a string.
- `enumerate`: Iterates over the default values of the input node.
- `isinstance`: Checks the type of the input node to determine the prefix of the function signature.
- `len`: Not explicitly used in the provided code snippet.
- `parts.append`: Appends argument names to a list.
- `unparsed.find`: Finds the index of the first colon and newline characters in the unparsed string.
- `unparsed.replace`: Removes the `: pass` statement from the unparsed string if the index is not found.

## Potential Considerations
The `_build_signature` function has the following potential considerations:
- Error handling: The function catches `AttributeError` and `TypeError` exceptions, but does not handle other potential exceptions that may occur during the execution of the traced calls.
- Edge cases: The function may not handle edge cases such as functions with no arguments, functions with only default arguments, or functions with complex argument types.
- Performance: The function uses the `ast.unparse` method to unparse the new node into a string, which may have performance implications for large input nodes.

## Signature
The signature of the `_build_signature` function is:
```python
def _build_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
```
This indicates that the function takes a single argument `node` of type `ast.FunctionDef` or `ast.AsyncFunctionDef` and returns a string representing the function signature.
---

# _parse_assign_targets

## Logic Overview
The `_parse_assign_targets` function takes an `ast.Assign` node as input and returns a list of strings representing the names extracted from the assignment targets. The main steps in the function are:
1. Initialize an empty list `names` to store the extracted names.
2. Iterate over each target in the `node.targets` list.
3. For each target, check if it is an instance of `ast.Name` or `ast.Tuple`.
4. If the target is an `ast.Name`, append its `id` to the `names` list.
5. If the target is an `ast.Tuple`, iterate over its elements and check if each element is an `ast.Name`. If so, append its `id` to the `names` list.
6. Return the `names` list.

## Dependency Interactions
The function uses the following traced calls:
- `isinstance`: This function is used to check the type of each target in the `node.targets` list. It is called with the following qualified names:
  - `ast.Name`
  - `ast.Tuple`
- `names.append`: This method is used to add the extracted names to the `names` list.
The function also uses the `ast.Assign` type from the `ast` module, which is not explicitly imported in the given code snippet but is likely imported from the `vivarium/scout/adapters/base.py` module.

## Potential Considerations
Based on the code, the following potential considerations can be identified:
- Edge cases: The function does not handle cases where the target is not an `ast.Name` or `ast.Tuple`. It simply ignores such targets.
- Error handling: The function does not include any explicit error handling. If an error occurs during the execution of the function, it will be propagated to the caller.
- Performance: The function has a time complexity of O(n), where n is the number of targets in the `node.targets` list. This is because it iterates over each target and its elements (in the case of tuples).

## Signature
The function signature is:
```python
def _parse_assign_targets(node: ast.Assign) -> List[str]:
```
This indicates that the function:
- Takes a single argument `node` of type `ast.Assign`.
- Returns a list of strings (`List[str]`).
The leading underscore in the function name suggests that it is intended to be a private function, not part of the public API.
---

# _is_simple_symbol

## Logic Overview
The `_is_simple_symbol` function determines whether a given `symbol` of type `SymbolTree` can be considered "simple" based on specific criteria. The main steps in the function's logic are:
1. Checking the symbol's type to ensure it is a function, method, or async function.
2. Examining the symbol's `logic_hints` for indicators of control flow (loop, conditional, exception handling).
3. Evaluating the number of lines in the symbol's body.
4. Inspecting the symbol's `calls` to verify they are only built-in calls.

## Dependency Interactions
The function interacts with the following traced calls and types:
- `any`: Used to check if any of the control flow hints are present in the `logic_hints`.
- `getattr`: Utilized to safely retrieve attributes (`logic_hints`, `calls`) from the `symbol` object, providing a default value if the attribute does not exist.
- `SymbolTree`: The type of the `symbol` parameter, indicating the function operates on a specific data structure.
- `vivarium/scout/adapters/base.py`: Although this import is mentioned, its direct interaction with the function is not explicitly shown in the provided code snippet. However, it might influence the definition or behavior of `SymbolTree` or other used types.

## Potential Considerations
- **Edge Cases**: The function does not handle potential edge cases such as `None` values for `symbol.lineno` or `symbol.end_lineno`, which could lead to errors when calculating `body_lines`.
- **Error Handling**: The function does not explicitly handle errors. For example, if `symbol` is not of type `SymbolTree`, or if `getattr` fails for any reason, the function may raise an exception.
- **Performance**: The function's performance seems to be linear with respect to the number of calls in the symbol, as it iterates over each call to check if it's a built-in call. However, the overall complexity is relatively low, making it efficient for most use cases.

## Signature
The function signature is `def _is_simple_symbol(symbol: SymbolTree) -> bool`. This indicates:
- The function is named `_is_simple_symbol`, starting with an underscore, which is a Python convention for indicating the function is intended to be private.
- It takes one parameter, `symbol`, which is expected to be of type `SymbolTree`.
- The function returns a boolean value (`bool`), indicating whether the symbol meets the criteria for being considered "simple".
---

# _extract_return_expr

## Logic Overview
The `_extract_return_expr` function takes a `source_snippet` as input and attempts to extract the expression from a single return statement. The main steps are:
1. Parse the `source_snippet` into an abstract syntax tree (AST) using `ast.parse`.
2. Traverse the AST using `ast.walk` to find a return statement with a non-None value.
3. If such a return statement is found, extract the expression using `ast.unparse` and return it.
4. If no return statement with a non-None value is found, or if a `SyntaxError` or `ValueError` occurs during parsing, return `None`.

## Dependency Interactions
The function interacts with the following dependencies:
* `ast.parse`: used to parse the `source_snippet` into an AST.
* `ast.walk`: used to traverse the AST and find return statements.
* `ast.unparse`: used to extract the expression from the return statement.
* `isinstance`: used to check if a node is an instance of `ast.Return`.
* `vivarium/scout/adapters/base.py`: imported, but not explicitly used in the function.

## Potential Considerations
The function has the following potential considerations:
* Error handling: the function catches `SyntaxError` and `ValueError` exceptions, but does not handle other potential exceptions that may occur during parsing or traversal.
* Edge cases: the function assumes that the `source_snippet` contains a single return statement with a non-None value. If the snippet contains multiple return statements or no return statements, the function may not behave as expected.
* Performance: the function uses `ast.walk` to traverse the entire AST, which may be inefficient for large snippets.

## Signature
The function signature is:
```python
def _extract_return_expr(source_snippet: str) -> Optional[str]
```
This indicates that the function:
* Takes a single argument `source_snippet` of type `str`.
* Returns a value of type `Optional[str]`, which means it may return either a string or `None`.
---

# try_auto_tldr

## Logic Overview
The `try_auto_tldr` function takes a `symbol` of type `SymbolTree` and a `source_snippet` of type `str` as input. The main steps in the function are:
1. Check if the `symbol` is simple using the `_is_simple_symbol` function.
2. If the `symbol` is not simple, return `None`.
3. If the `symbol` is simple, extract the return expression from the `source_snippet` using the `_extract_return_expr` function.
4. If a return expression is found, return a string in the format "Returns {expr}."
5. If no return expression is found, return a string in the format "Simple {name} utility."

## Dependency Interactions
The `try_auto_tldr` function uses the following traced calls:
- `vivarium.scout.adapters.base._is_simple_symbol(symbol)`: This function is used to check if the `symbol` is simple.
- `vivarium.scout.adapters.base._extract_return_expr(source_snippet)`: This function is used to extract the return expression from the `source_snippet`.

## Potential Considerations
Based on the code, the following potential considerations can be identified:
- **Edge case:** If the `symbol` is not simple, the function returns `None`. This might be a valid use case, but it's worth considering if there are other possible actions that could be taken in this scenario.
- **Error handling:** The function does not appear to handle any errors that might occur when calling the `_is_simple_symbol` or `_extract_return_expr` functions. It's possible that these functions could raise exceptions, which would need to be handled.
- **Performance:** The function makes two function calls, which could potentially impact performance if the function is called frequently. However, without more information about the implementation of these functions, it's difficult to say for certain.

## Signature
The `try_auto_tldr` function has the following signature:
```python
def try_auto_tldr(symbol: SymbolTree, source_snippet: str) -> Optional[str]
```
This indicates that the function:
- Takes two parameters: `symbol` of type `SymbolTree` and `source_snippet` of type `str`.
- Returns a value of type `Optional[str]`, which means it can return either a string or `None`.
---

# PythonAdapter

## Logic Overview
The `PythonAdapter` class is designed to parse Python files using Abstract Syntax Tree (AST) parsing. The main steps in the code are:
1. Checking if the target file exists and is a Python file.
2. Reading the file content and parsing it using the `ast.parse` function.
3. Extracting import maps, module exports, and processing callable and class definitions.
4. Creating a `SymbolTree` object to represent the parsed module.

The `parse` method is the core of the class, responsible for parsing the Python file and creating the `SymbolTree` object. It uses several helper functions, such as `_build_import_map`, `_extract_module_exports`, `process_callable`, and `process_class`, to extract relevant information from the AST.

## Dependency Interactions
The `PythonAdapter` class uses the traced calls to interact with dependencies in the following ways:
1. **Importing modules**: The `_build_import_map` function is used to extract import statements from the AST, which are then used to create a map of imported modules.
2. **Calling functions**: The `process_callable` function extracts calls from the AST and creates a list of called functions, which are then stored in the `SymbolTree` object.
3. **Using types**: The `_extract_types_from_node` function is used to extract types from the AST, which are then stored in the `SymbolTree` object.

The class uses the traced calls to reference qualified names, such as function calls and type usage, to create a detailed representation of the parsed module.

## Potential Considerations
The `PythonAdapter` class handles several potential edge cases and errors:
1. **File not found**: The class raises a `FileNotFoundError` if the target file does not exist.
2. **Invalid Python file**: The class raises a `ValueError` if the target file is not a Python file.
3. **Syntax errors**: The class raises a `SyntaxError` if the Python file contains syntax errors.
4. **Unicode decoding errors**: The class raises a `UnicodeDecodeError` if there are issues with decoding the file content.
5. **IO errors**: The class raises an `IOError` if there are issues with reading the file content.

The class also considers performance by using efficient data structures, such as lists and dictionaries, to store extracted information.

## Signature
N/A

Note: The `get_tldr_prompt`, `get_deep_prompt`, and `get_eliv_prompt` methods are used to generate prompts for different types of analysis, but they do not affect the overall logic and dependency interactions of the `PythonAdapter` class.
---

# extensions

## Logic Overview
The `extensions` method is defined to return a list of strings, specifically file extensions. The method contains a single return statement that provides a list containing one string, `".py"`, which is the file extension for Python files. The logic flow is straightforward, with no conditional statements or loops, and it directly returns the specified list.

## Dependency Interactions
There are no traced calls to other methods or functions within the provided `extensions` method. However, it uses the `List[str]` type hint, which is not explicitly imported in the given source code but is likely imported from the `typing` module, which is a standard Python module. The method does not directly interact with any of the traced imports, such as `vivarium/scout/adapters/base.py`.

## Potential Considerations
The method does not handle any potential errors, as it simply returns a predefined list. There are no edge cases explicitly addressed within the method, such as handling different types of input or checking for specific conditions. The performance of the method is straightforward and efficient, as it involves a single return statement with a predefined list. However, the method's purpose and context within a larger application or system are not clear from the provided code.

## Signature
The `extensions` method is defined with the following signature: `def extensions(self) -> List[str]`. This indicates that the method:
- Is an instance method, as denoted by the `self` parameter.
- Returns a list of strings, as specified by the `-> List[str]` type hint.
- Does not take any additional parameters beyond the implicit `self` reference to the instance of the class.
---

# parse

## Logic Overview
The `parse` method is designed to parse a Python file and return a `SymbolTree` object representing the file's structure. The main steps in the code are:
1. **File Validation**: The method checks if the provided `file_path` exists and is a Python file. If not, it raises a `FileNotFoundError` or `ValueError`.
2. **File Reading**: It attempts to read the file's content using `file_path.read_text`. If there's an issue with decoding, it raises a `UnicodeDecodeError` or `IOError`.
3. **AST Parsing**: The method uses `ast.parse` to parse the file's content into an Abstract Syntax Tree (AST).
4. **Import Map and Module Exports**: It builds an import map using `_build_import_map` and extracts module exports using `_extract_module_exports`.
5. **Symbol Tree Construction**: The method iterates over the AST nodes, processing functions, classes, and assignments to construct a `SymbolTree` object.
6. **Return**: Finally, it returns the constructed `SymbolTree` object representing the module.

## Dependency Interactions
The `parse` method interacts with the following traced calls:
* `FileNotFoundError`: raised when the target file is not found.
* `IOError`: raised when there's an issue reading the file.
* `UnicodeDecodeError`: raised when there's an issue decoding the file's content.
* `SyntaxError`: raised when there's a syntax error in the file's content.
* `ValueError`: raised when the target is not a Python file.
* `_build_import_map`: used to build an import map from the AST.
* `_build_signature`: used to build a signature for a function or method.
* `_extract_calls_from_body`: used to extract calls from a function or class body.
* `_extract_logic_hints`: used to extract logic hints from a function or class.
* `_extract_module_exports`: used to extract module exports from the AST.
* `_extract_types_from_node`: used to extract types from a node.
* `_parse_assign_targets`: used to parse assign targets from an assignment node.
* `ast.get_docstring`: used to get the docstring of a node.
* `ast.iter_child_nodes`: used to iterate over the child nodes of the AST.
* `ast.parse`: used to parse the file's content into an AST.
* `pathlib.Path`: used to resolve the file path and check if it's a file.

## Potential Considerations
Some potential considerations and edge cases in the code are:
* **Error Handling**: The method raises specific exceptions for different error cases, such as file not found, decoding errors, and syntax errors.
* **Performance**: The method uses recursive functions to process the AST nodes, which could potentially lead to performance issues for large files.
* **Edge Cases**: The method assumes that the file's content is a valid Python syntax. If the file contains invalid syntax, it will raise a `SyntaxError`.
* **Import Map**: The method builds an import map using `_build_import_map`, which could potentially lead to issues if the import map is not correctly constructed.

## Signature
The `parse` method has the following signature:
```python
def parse(self, file_path: Path) -> SymbolTree
```
This indicates that the method takes a `file_path` parameter of type `Path` and returns a `SymbolTree` object. The `self` parameter is a reference to the instance of the class that this method is a part of.
---

# try_auto_tldr

## Logic Overview
The `try_auto_tldr` function takes a `symbol` of type `SymbolTree` and a `source_snippet` of type `str` as input. The main steps in the function are:
1. Check if the `symbol` is simple using the `_is_simple_symbol` function.
2. If the `symbol` is not simple, return `None`.
3. If the `symbol` is simple, extract the return expression from the `source_snippet` using the `_extract_return_expr` function.
4. If a return expression is found, return a string in the format "Returns {expr}."
5. If no return expression is found, return a string in the format "Simple {name} utility."

## Dependency Interactions
The `try_auto_tldr` function uses the following traced calls:
- `vivarium.scout.adapters.base._is_simple_symbol(symbol)`: This function is used to check if the `symbol` is simple.
- `vivarium.scout.adapters.base._extract_return_expr(source_snippet)`: This function is used to extract the return expression from the `source_snippet`.

## Potential Considerations
Based on the code, the following potential considerations can be identified:
- **Edge case:** If the `symbol` is not simple, the function returns `None`. This might be a valid use case, but it's worth considering if there are other possible actions that could be taken in this scenario.
- **Error handling:** The function does not appear to handle any errors that might occur when calling the `_is_simple_symbol` or `_extract_return_expr` functions. It's possible that these functions could raise exceptions, which would need to be handled.
- **Performance:** The function makes two function calls, which could potentially impact performance if the function is called frequently. However, without more information about the implementation of these functions, it's difficult to say for certain.

## Signature
The `try_auto_tldr` function has the following signature:
```python
def try_auto_tldr(symbol: SymbolTree, source_snippet: str) -> Optional[str]
```
This indicates that the function:
- Takes two parameters: `symbol` of type `SymbolTree` and `source_snippet` of type `str`.
- Returns a value of type `Optional[str]`, which means it can return either a string or `None`.
---

# get_tldr_prompt

## Logic Overview
The `get_tldr_prompt` method takes in a `symbol` of type `SymbolTree` and a list of `dependencies` as strings. It then extracts the following information from the `symbol`:
- `calls`: a list of qualified calls made by the symbol
- `uses_types`: a list of types used by the symbol
- `exports`: a list of exports from the symbol

The method then formats this information into strings:
- `calls_str`: a string representation of the calls, with each call on a new line, or "(none traced)" if there are no calls
- `types_str`: a comma-separated string of the types used, or "none" if there are no types used
- `exports_str`: a comma-separated string of the exports, or "(none)" if there are no exports

Finally, the method returns a formatted string that includes the symbol's name, exports, calls, types used, and dependencies, along with a prompt to write a concise summary of the symbol's role in the system.

## Dependency Interactions
The method uses the `getattr` function to access the `calls`, `uses_types`, and `exports` attributes of the `symbol` object. If any of these attributes do not exist, `getattr` returns `None`, and the method uses an empty list as a default value.

The method also uses the `dependencies` list to include the dependencies of the symbol in the output string.

## Potential Considerations
- The method does not handle any potential errors that may occur when accessing the attributes of the `symbol` object.
- The method assumes that the `calls`, `uses_types`, and `exports` attributes of the `symbol` object are lists. If they are not, the method may raise an error when trying to join them into strings.
- The method does not check if the `dependencies` list is empty before trying to join it into a string. However, the code does handle this case by using the `', '.join(dependencies) if dependencies else 'none'` expression.
- The performance of the method is likely to be good, as it only accesses a few attributes of the `symbol` object and performs some simple string formatting.

## Signature
The `get_tldr_prompt` method has the following signature:
```python
def get_tldr_prompt(self, symbol: SymbolTree, dependencies: List[str]) -> str:
```
This signature indicates that:
- The method is an instance method (i.e., it is called on an instance of a class) because it takes `self` as its first parameter.
- The method takes two parameters: `symbol` of type `SymbolTree` and `dependencies` of type `List[str]`.
- The method returns a string.
---

# get_deep_prompt

## Logic Overview
The `get_deep_prompt` method appears to be designed to generate a formatted string containing information about a given `symbol` of type `SymbolTree`. The method's flow can be broken down into the following main steps:
1. It retrieves the `calls` and `uses_types` attributes from the `symbol` object using the `getattr` function, providing default values of `None` or empty lists if these attributes do not exist.
2. It constructs two strings, `calls_str` and `types_str`, based on the `calls` and `uses_types` attributes, respectively. These strings are formatted to display the calls and types in a human-readable format.
3. It returns a formatted string containing the analyzed information, including the symbol type and name, traced facts (calls and uses types), imports (dependencies), and source code snippet.

## Dependency Interactions
The method interacts with the following dependencies:
- `symbol`: an object of type `SymbolTree`, which has attributes such as `calls`, `uses_types`, `type`, and `name`.
- `dependencies`: a list of strings representing the dependencies or imports.
- `source_snippet`: a string containing the source code snippet to be analyzed.
- `getattr`: a built-in Python function used to retrieve the `calls` and `uses_types` attributes from the `symbol` object.
- `vivarium/scout/adapters/base.py`: an imported module, although its specific usage is not directly visible in the provided code snippet.

## Potential Considerations
Some potential considerations and edge cases to note:
- **Error Handling**: The method does not appear to have explicit error handling. For example, if the `symbol` object is `None` or does not have the expected attributes, the method may raise an exception.
- **Performance**: The method's performance is likely to be acceptable for most use cases, as it only involves simple string manipulation and attribute retrieval. However, if the `calls` or `uses_types` lists are extremely large, the string construction process could potentially become a bottleneck.
- **Edge Cases**: The method assumes that the `symbol` object has certain attributes (e.g., `calls`, `uses_types`, `type`, and `name`). If these attributes are missing or have unexpected values, the method's behavior may be incorrect or unpredictable.

## Signature
The method signature is:
```python
def get_deep_prompt(self, symbol: SymbolTree, dependencies: List[str], source_snippet: str) -> str
```
This signature indicates that the method:
- Is an instance method (due to the `self` parameter)
- Takes three parameters: `symbol` of type `SymbolTree`, `dependencies` of type `List[str]`, and `source_snippet` of type `str`
- Returns a string value (`-> str`)
---

# get_eliv_prompt

## Logic Overview
The `get_eliv_prompt` method takes in three parameters: `symbol`, `dependencies`, and `source_snippet`. It first checks if the `symbol` object has a `calls` attribute. If it does, it retrieves the first 5 calls and converts them into a string. If not, it sets the string to "nothing specific". Then, it constructs a prompt string that includes information about the `symbol`, its type, name, calls, dependencies, and the provided `source_snippet`.

## Dependency Interactions
The method uses the `getattr` function to interact with the `symbol` object. Specifically, it calls `getattr(symbol, "calls", None)` to retrieve the `calls` attribute from the `symbol` object. If the attribute does not exist, `getattr` returns `None`.

## Potential Considerations
The method does not appear to handle any potential errors that may occur when retrieving the `calls` attribute or constructing the prompt string. It also assumes that the `symbol` object has a `type` and `name` attribute, which may not always be the case. Additionally, the method truncates the list of calls and dependencies to 5 items, which may not be sufficient for all use cases.

## Signature
The method signature is `def get_eliv_prompt(self, symbol: SymbolTree, dependencies: List[str], source_snippet: str) -> str`. This indicates that the method:
- Is an instance method (due to the `self` parameter)
- Takes in three parameters: `symbol` of type `SymbolTree`, `dependencies` of type `List[str]`, and `source_snippet` of type `str`
- Returns a string value (`-> str`)
---

# symbol_to_dict

## Logic Overview
The `symbol_to_dict` function takes a `SymbolTree` object as input and returns a dictionary representation of it. The function's main step is to create a dictionary with specific keys and assign the corresponding values from the `SymbolTree` object. The keys in the dictionary include "name", "type", "lineno", "end_lineno", "docstring", "signature", and "logic_hints".

## Dependency Interactions
The function uses the `SymbolTree` type, which is not explicitly imported in the given code snippet. However, based on the traced imports, it is likely that `SymbolTree` is imported from `vivarium/scout/adapters/base.py`. The function does not make any explicit calls to other functions or methods, but it accesses attributes of the `SymbolTree` object, such as `symbol.name`, `symbol.type`, etc.

## Potential Considerations
The function does not appear to handle any potential errors that may occur when accessing the attributes of the `SymbolTree` object. If any of these attributes are missing or have incorrect types, the function may raise an `AttributeError` or a `TypeError`. Additionally, the function does not perform any validation on the input `SymbolTree` object, which could lead to issues if the object is not in a valid state. In terms of performance, the function has a constant time complexity, as it only accesses a fixed set of attributes and creates a dictionary with a fixed set of keys.

## Signature
The function signature is `def symbol_to_dict(symbol: SymbolTree) -> Dict[str, Any]`. This indicates that the function takes a single argument `symbol` of type `SymbolTree` and returns a dictionary with string keys and values of any type. The use of `Dict[str, Any]` as the return type suggests that the function is designed to be flexible and can handle a wide range of possible values in the output dictionary.