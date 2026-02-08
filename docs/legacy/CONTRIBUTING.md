## Running the Test Suite

Before committing any changes, ensure the full test suite passes:

```bash
pytest
```

If you have installed the repository’s Git hooks (see the README), this will be executed automatically on every `git commit`.
## Running Tests & CI

The project uses **pytest** with coverage enforcement.

```bash
# Install development dependencies
## Branch Protection & CI Requirements

- All pull requests **must** pass the GitHub Actions **CI** workflow before they can be merged.
- At least one approved review is required.
- Direct pushes to `main` and `develop` are prohibited for non‑maintainers.
- The repository uses a **linear history**; rebase before merge is encouraged.
pip install -r requirements-dev.txt

# Run the full test suite with coverage
pytest --cov=src

# View a detailed coverage report
coverage report -m
```

### Pre‑commit Hook

A lightweight pre‑commit hook is provided in `.githooks/pre-commit`. To enable it:

```bash
ln -s ../../.githooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

This hook will block any commit that fails the test suite, ensuring that **no code reaches the remote repository without passing tests**.

### CI Checks

All pull requests trigger the GitHub Actions workflow defined in `.github/workflows/ci.yml`. The workflow runs:

1. **Lint** – `flake8` and `black --check`.  
2. **Test** – `pytest` with a minimum **85 %** coverage requirement.  
3. **Build** – Packaging sanity check.

The repository’s branch protection rules now require these checks to pass before a merge is allowed.