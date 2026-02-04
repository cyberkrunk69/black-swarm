"""
Utility that binds Pydantic output schemas to the role classes.
This avoids direct modification of the protected `roles.py` file.
"""

from .schemas import TaskAssignment, ExecutionPlan, CodeArtifact, ReviewFeedback
import importlib

# Dynamically import the roles module (assumed to be at app.roles)
roles_module = importlib.import_module("app.roles")

# Map role class names to their corresponding output schemas
_schema_map = {
    "TaskAssigner": TaskAssignment,
    "Planner": ExecutionPlan,
    "Executor": CodeArtifact,
    "Reviewer": ReviewFeedback,
}

# Attach the schemas as a class attribute `output_schema`
for role_name, schema_cls in _schema_map.items():
    role_cls = getattr(roles_module, role_name, None)
    if role_cls is not None:
        setattr(role_cls, "output_schema", schema_cls)