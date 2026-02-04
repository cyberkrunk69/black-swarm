import inspect
from .skill_registry import register_skill
from .import_config_constants import import_config_constants
from .migrate_to_utils import migrate_to_utils
from .add_test_coverage import add_test_coverage

def __register_skills():
    register_skill(
        name="import_config_constants",
        code=inspect.getsource(import_config_constants),
        description="Import configuration constants from a JSON file into globals.",
        preconditions=["config.json exists"],
        postconditions=["globals contain config keys"]
    )
    register_skill(
        name="migrate_to_utils",
        code=inspect.getsource(migrate_to_utils),
        description="Migrate helper functions into a utils package.",
        preconditions=["helper functions identified"],
        postconditions=["helpers moved to utils/helpers.py"]
    )
    register_skill(
        name="add_test_coverage",
        code=inspect.getsource(add_test_coverage),
        description="Create a skeleton pytest file for a module.",
        preconditions=["module exists"],
        postconditions=["tests/test_<module>.py created"]
    )

# Register on import
__register_skills()
# Initialize skill registry with built-in skills
from .skill_registry import register_skill
from .import_config_constants import import_config_constants
from .migrate_to_utils import migrate_to_utils
from .add_test_coverage import add_test_coverage

register_skill(
    name="import_config_constants",
    code=import_config_constants,
    description="Import selected constants from a config module into globals.",
    preconditions=["config module is imported", "constants list provided"],
    postconditions=["globals contain the imported constants"]
)

register_skill(
    name="migrate_to_utils",
    code=migrate_to_utils,
    description="Migrate specified symbols from old module to utils module.",
    preconditions=["old module and utils module are importable", "names list provided"],
    postconditions=["utils module now contains the symbols, old module no longer has them"]
)

register_skill(
    name="add_test_coverage",
    code=add_test_coverage,
    description="Add test coverage for a target module.",
    preconditions=["test suite is available", "target module is importable"],
    postconditions=["test suite includes new tests for target module"]
)
# skills package initializer