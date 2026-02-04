#!/usr/bin/env bash
# Self‑integration pipeline for experimental code.
# -------------------------------------------------
# 1. Verify there are uncommitted changes in the `experiments/` directory.
# 2. Run linting and tests to validate the changes.
# 3. Create a short‑lived feature branch, commit the changes, and push.
# 4. Open a Pull Request against the default branch using the GitHub CLI.
# -------------------------------------------------
set -euo pipefail

# Configuration
BASE_BRANCH="${BASE_BRANCH:-main}"
EXPERIMENTS_DIR="experiments"
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
BRANCH_NAME="auto/integrate-${TIMESTAMP}"
PR_TITLE="Auto‑integrate experimental changes (${TIMESTAMP})"
PR_BODY="This PR was generated automatically by \`scripts/integrate.sh\`. It includes validated changes from the \`${EXPERIMENTS_DIR}\` folder."

# Step 1: Detect changes
if ! git diff --quiet --exit-code -- "${EXPERIMENTS_DIR}"; then
    echo "Detected changes in ${EXPERIMENTS_DIR}."
else
    echo "No changes detected in ${EXPERIMENTS_DIR}. Exiting."
    exit 0
fi

# Step 2: Lint & Test
if command -v npm >/dev/null 2>&1; then
    echo "Running npm install..."
    npm ci
    echo "Running lint..."
    npm run lint --if-present
    echo "Running tests..."
    npm test --if-present
else
    echo "npm not found – skipping lint and test steps."
fi

# Step 3: Create branch, commit, push
git checkout -b "${BRANCH_NAME}" "${BASE_BRANCH}"
git add "${EXPERIMENTS_DIR}"
git commit -m "chore: integrate experimental changes"
git push -u origin "${BRANCH_NAME}"

# Step 4: Open PR (requires GitHub CLI `gh`)
if command -v gh >/dev/null 2>&1; then
    echo "Creating Pull Request via gh..."
    gh pr create \
        --base "${BASE_BRANCH}" \
        --head "${BRANCH_NAME}" \
        --title "${PR_TITLE}" \
        --body "${PR_BODY}" \
        --label "auto‑integrate"
else
    echo "GitHub CLI (gh) not installed – PR must be opened manually."
fi