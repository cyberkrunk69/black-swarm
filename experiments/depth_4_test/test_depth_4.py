import logging
from recursive_improvement_engine import RecursiveImprovementEngine

logging.basicConfig(level=logging.INFO)

# --------------------------------------------------------------------- #
# Mock builder implementations for demonstration purposes
# --------------------------------------------------------------------- #
def atomizer_builder(prev):
    # Simulate a 5x efficiency improvement
    class Artifact:
        def __init__(self, efficiency):
            self.efficiency = efficiency
            self.score = efficiency
    return Artifact(prev.efficiency * 5)

def task_builder(prev):
    # Simulate a modest 1.2x improvement on top of atomizer
    class Artifact:
        def __init__(self, efficiency):
            self.efficiency = efficiency
            self.score = efficiency
    return Artifact(prev.efficiency * 1.2)

def meta_builder(prev):
    # Simulate a 1.1x improvement
    class Artifact:
        def __init__(self, efficiency):
            self.efficiency = efficiency
            self.score = efficiency
    return Artifact(prev.efficiency * 1.1)

def architecture_evolver(prev):
    # Simulate a 1.05x improvement
    class Artifact:
        def __init__(self, efficiency):
            self.efficiency = efficiency
            self.score = efficiency
    return Artifact(prev.efficiency * 1.05)

# --------------------------------------------------------------------- #
# Initialise engine and register builders
# --------------------------------------------------------------------- #
engine = RecursiveImprovementEngine()
engine.register_builder(1, atomizer_builder)
engine.register_builder(2, task_builder)
engine.register_builder(3, meta_builder)
engine.register_builder(4, architecture_evolver)

# Seed artifact (depth 0)
class Seed:
    def __init__(self):
        self.efficiency = 1.0
        self.score = 1.0

final_artifact = engine.run(Seed())
print(f"Final efficiency after recursive improvement: {final_artifact.efficiency}")