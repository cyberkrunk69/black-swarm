def migrate_to_utils():
    """Move reusable helpers into a utils module.
    Extracted from *utils_migration_lessons*.
    It creates a ``utils`` package if missing and moves functions there,
    updating imports accordingly.
    """
    import pathlib
    import os

    src_dir = pathlib.Path.cwd()
    utils_dir = src_dir / "utils"
    utils_dir.mkdir(exist_ok=True)

    # Example: move all functions prefixed with ``_helper_`` into utils/helpers.py
    helper_files = [p for p in src_dir.rglob("*.py") if p.name != "helpers.py"]
    for file in helper_files:
        with file.open() as f:
            content = f.read()
        # naive detection
        if "_helper_" in content:
            dest = utils_dir / "helpers.py"
            with dest.open("a") as df:
                df.write("\n" + content)
            os.remove(file)
def migrate_to_utils(old_module, utils_module, names):
    """
    Move specified functions or classes from old_module to utils_module.
    - old_module: module where items currently reside
    - utils_module: target utils module
    - names: list of attribute names to migrate
    """
    for name in names:
        if hasattr(old_module, name):
            attr = getattr(old_module, name)
            setattr(utils_module, name, attr)
            delattr(old_module, name)
# skills/migrate_to_utils.py

skill_code = \"\"\"
def migrate_to_utils():
    \"\"\"Move shared helper functions into a central utils module and update imports.\"\"\"
    # Example pattern (to be adapted per project):
    # 1. Identify duplicate functions.
    # 2. Cut them into utils.py.
    # 3. Replace original definitions with: from utils import <function_name>
\"\"\"

from .skill_registry import register_skill

register_skill(
    name="migrate_to_utils",
    code=skill_code,
    description="Migrate duplicated helpers to a utils module and adjust imports.",
    preconditions=[],
    postconditions=[],
)
# skills/migrate_to_utils.py
"""
Skill to migrate reusable functions into the utils package.
"""

def migrate_to_utils(source_path: str, target_module: str):
    \"\"\"Move a function definition from source_path to utils/target_module.py.\"\"\"
    import ast, os, shutil, textwrap

    with open(source_path, "r", encoding="utf-8") as f:
        source_code = f.read()
    tree = ast.parse(source_code)

    # Find the first function definition (simplified heuristic)
    func_node = next((n for n in tree.body if isinstance(n, ast.FunctionDef)), None)
    if not func_node:
        raise ValueError("No function definition found in source file.")

    func_code = ast.get_source_segment(source_code, func_node)
    if not func_code:
        raise RuntimeError("Failed to extract function source.")

    utils_dir = os.path.join(os.path.dirname(source_path), "..", "utils")
    os.makedirs(utils_dir, exist_ok=True)
    target_path = os.path.join(utils_dir, f"{target_module}.py")

    # Append or create the utils module
    with open(target_path, "a", encoding="utf-8") as tf:
        tf.write("\\n\\n")
        tf.write(textwrap.dedent(func_code))

    # Optionally remove the original function (naïve line removal)
    lines = source_code.splitlines()
    start = func_node.lineno - 1
    end = func_node.end_lineno
    remaining = lines[:start] + lines[end:]
    with open(source_path, "w", encoding="utf-8") as sf:
        sf.write("\\n".join(remaining))

    return {"migrated_function": func_node.name, "target": target_path}

# Register the skill
from .skill_registry import register_skill
register_skill(
    name="migrate_to_utils",
    func=migrate_to_utils,
    description="Migrate a function from a source file into a utils module.",
    preconditions=["source_path exists", "function present in source"],
    postconditions=["function available in utils module"]
)
def migrate_to_utils(old_module, utils_module, function_names):
    """
    Move specified functions from an old module into a shared utils module.

    Args:
        old_module: Module object containing the original functions.
        utils_module: Module object that will receive the functions.
        function_names: Iterable of function name strings to migrate.
    """
    for func_name in function_names:
        if hasattr(old_module, func_name):
            func = getattr(old_module, func_name)
            setattr(utils_module, func_name, func)
            delattr(old_module, func_name)
        else:
            raise AttributeError(f"Old module missing function: {func_name}")
def migrate_to_utils():
    """
    Pattern for migrating reusable functions into the ``utils`` package.
    This stub demonstrates the typical steps (update imports, move code).
    """
    # Example transformation:
    #   from old_module import helper
    #   → from utils.helper import helper
    pass
from .skill_registry import register_skill
import shutil
import os

def migrate_to_utils(source_path, utils_dir):
    \"\"\"Pattern: move reusable helpers into a utils package.\"\"\"
    if not os.path.isdir(utils_dir):
        os.makedirs(utils_dir)
    shutil.move(source_path, utils_dir)

# Register the skill
register_skill(
    name="migrate_to_utils",
    code=migrate_to_utils.__code__.co_code.hex(),
    description="Move a module or file into the project's utils directory.",
    preconditions=["source_path exists", "utils_dir is writable"],
    postconditions=["module is located inside utils"]
)