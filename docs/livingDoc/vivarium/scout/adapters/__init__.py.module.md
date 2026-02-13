## Purpose — What this package does
The vivarium.scout.adapters package provides adapters for various file formats, including JavaScript, plain text, and Python, to process and analyze symbolic data.

## Components — Ingress/Processing/Egress
### Ingress
- `javascript.py`: Handles JavaScript files, parsing and extracting imports.
- `plain_text.py`: Handles plain text files, reading and processing file content.
- `python.py`: Handles Python files, parsing and extracting import statements.

### Processing
- `base.py`: Provides a base class for adapters, including SymbolTree and LanguageAdapter, and utility functions for extensions and parsing.

### Egress
- `registry.py`: Exports functions for getting adapters and supported extensions, and ensures the registry is properly set up.

## Key Invariants — Constraints from the code
- The package does not have any external dependencies.
- The `plain_text.py` adapter logs warnings for file-related issues.
- The `python.py` adapter builds an import map from the AST of a Python module.
- The `javascript.py` adapter uses a regular expression to extract import statements and recursively traverses a JavaScript tree structure for documentation purposes.