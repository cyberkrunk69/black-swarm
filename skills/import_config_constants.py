def import_config_constants():
    """Import configuration constants into the current namespace.
    This pattern was extracted from the *config_integration_lessons*.
    It reads a JSON/YAML config file and injects its keys as globals.
    """
    import json
    import pathlib

    config_path = pathlib.Path(__file__).parent / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open() as f:
        cfg = json.load(f)

    globals().update(cfg)
def import_config_constants(config_module, constants):
    """
    Import specified constants from a configuration module into the current globals.
    - config_module: imported module object (e.g., import config)
    - constants: list of constant names to import
    """
    globals_ = globals()
    for name in constants:
        if hasattr(config_module, name):
            globals_[name] = getattr(config_module, name)
# skills/import_config_constants.py

skill_code = \"\"\"
def import_config_constants():
    \"\"\"Import all constants from the project's config module into the current namespace.\"\"\"
    from config import *
\"\"\"

from .skill_registry import register_skill

register_skill(
    name="import_config_constants",
    code=skill_code,
    description="Import configuration constants from the config module.",
    preconditions=[],
    postconditions=[],
)
# skills/import_config_constants.py
"""
Skill to import configuration constants from the project's config module.
"""

def import_config_constants():
    \"\"\"Return a dictionary of configuration constants.\"\"\"
    from config import CONFIG_CONSTANTS  # type: ignore
    return CONFIG_CONSTANTS

# Register the skill
from .skill_registry import register_skill
register_skill(
    name="import_config_constants",
    func=import_config_constants,
    description="Import configuration constants from the project's config module.",
    preconditions=[],
    postconditions=["Returns a dict of constants"]
)
def import_config_constants(target_module, config_module, constants):
    """
    Import specified configuration constants from a config module into a target module.

    Args:
        target_module: Module object where constants will be injected.
        config_module: Module object that holds the source constants.
        constants: Iterable of constant names (strings) to import.
    """
    for const in constants:
        if hasattr(config_module, const):
            setattr(target_module, const, getattr(config_module, const))
        else:
            raise AttributeError(f"Config module missing constant: {const}")
def import_config_constants():
    """
    Load configuration constants from the project's ``config`` module.
    Returns the SETTINGS object for downstream use.
    """
    from config import SETTINGS
    return SETTINGS
from .skill_registry import register_skill

def import_config_constants():
    \"\"\"Pattern: centralise configuration constants via a single import point.\"\"\"
    # Example implementation – adapt paths as needed
    import json
    import os

    CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "constants.json")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        constants = json.load(f)
    globals().update(constants)

# Register the skill
register_skill(
    name="import_config_constants",
    code=import_config_constants.__code__.co_code.hex(),
    description="Import project‑wide configuration constants from JSON.",
    preconditions=["constants.json exists"],
    postconditions=["constants are available in globals()"]
)
# Skill: import_config_constants
SKILL_NAME = "import_config_constants"
DESCRIPTION = "Import configuration constants from a central config module into a target module."
PRECONDITIONS = ["config module exists", "target module can be edited"]
POSTCONDITIONS = ["constants are available via direct import in the target module"]

def skill(target_file_path: str, config_module: str = "config") -> str:
    """
    Insert an ``from <config_module> import <CONST>`` statement for every
    uppercase name defined in the config module, placing the import after any
    module docstring and existing imports.
    Returns the path of the modified file.
    """
    import ast
    import os

    # Helper to turn an AST back into source code without external deps
    def ast_to_source(tree):
        try:
            import astor  # type: ignore
            return astor.to_source(tree)
        except Exception:
            return ast.unparse(tree)  # Python 3.9+

    # Load target file
    with open(target_file_path, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source)

    # Load config module and collect uppercase names
    const_names = []
    try:
        config_path = config_module.replace(".", os.sep) + ".py"
        with open(config_path, "r", encoding="utf-8") as cf:
            config_src = cf.read()
        config_tree = ast.parse(config_src)
        for node in config_tree.body:
            if (
                isinstance(node, ast.Assign)
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id.isupper()
            ):
                const_names.append(node.targets[0].id)
    except Exception:
        # If we cannot read the config, fall back to an empty import list
        const_names = []

    if const_names:
        import_node = ast.ImportFrom(
            module=config_module,
            names=[ast.alias(name=name, asname=None) for name in const_names],
            level=0,
        )

        # Determine insertion point (after docstring and existing imports)
        insert_pos = 0
        for idx, node in enumerate(tree.body):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
                insert_pos = idx + 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                insert_pos = idx + 1
            else:
                break
        tree.body.insert(insert_pos, import_node)

        # Write back modified source
        new_source = ast_to_source(tree)
        with open(target_file_path, "w", encoding="utf-8") as f:
            f.write(new_source)

    return target_file_path