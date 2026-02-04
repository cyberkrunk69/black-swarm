import unittest
import sys
import pathlib

# Ensure the repository root is on the path
repo_root = pathlib.Path(__file__).resolve().parents[2]
sys.path.append(str(repo_root))

# Discover and run the benchmark tests
loader = unittest.TestLoader()
suite = loader.discover(start_dir=str(repo_root / "benchmarks"))
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

if not result.wasSuccessful():
    sys.exit(1)