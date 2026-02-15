#!/usr/bin/env bash
set -u -o pipefail

# Apply strict branch protection to master/main for owner-controlled merges.
# Usage:
#   ./devtools/apply-branch-protection.sh [owner/repo] [owner-login]

REPO="${1:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"
POLICY_OWNER="${2:-cyberkrunk69}"

REQUIRED_CHECKS=("policy" "tests" "integration" "lint")

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required." >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "gh is not authenticated. Run: gh auth login" >&2
  exit 1
fi

echo "Applying protection for repo: $REPO"
echo "Owner-locking push access to: $POLICY_OWNER"
echo "Required checks: ${REQUIRED_CHECKS[*]}"
echo ""

ADMIN_PERMISSION="$(gh api "repos/$REPO" --jq '.permissions.admin' 2>/dev/null || echo "unknown")"
if [[ "$ADMIN_PERMISSION" != "true" ]]; then
  echo "⚠️  Current token likely lacks repository admin rights (permissions.admin=$ADMIN_PERMISSION)."
  echo "   Branch protection updates require admin access."
  echo ""
fi

apply_branch_protection() {
  local branch="$1"
  local payload_file
  local output_file
  payload_file="$(mktemp)"
  output_file="$(mktemp)"

  cat >"$payload_file" <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["policy", "tests", "integration", "lint"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1,
    "require_last_push_approval": true
  },
  "restrictions": {
    "users": ["$POLICY_OWNER"],
    "teams": [],
    "apps": []
  },
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": true
}
EOF

  echo "  -> Protecting branch '$branch'"
  if gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "repos/$REPO/branches/$branch/protection" \
    --input "$payload_file" >"$output_file" 2>&1; then
    echo "     ✅ Protection updated for '$branch'"
    rm -f "$payload_file" "$output_file"
    return 0
  fi

  echo "     ❌ Failed to update '$branch'"
  cat "$output_file"
  if rg -q "Resource not accessible by integration|403" "$output_file"; then
    echo ""
    echo "     Remediation:"
    echo "       1) Authenticate gh with a PAT that has repo admin rights."
    echo "       2) Re-run this script from an owner/admin shell."
    echo "       3) Confirm settings in GitHub UI: Settings -> Branches."
  fi

  rm -f "$payload_file" "$output_file"
  return 1
}

FAILED=0
for branch in master main; do
  if gh api "repos/$REPO/branches/$branch" >/dev/null 2>&1; then
    if ! apply_branch_protection "$branch"; then
      FAILED=1
    fi
  else
    echo "  -> Skipping '$branch' (branch does not exist)"
  fi
done

echo ""
if [[ "$FAILED" -eq 0 ]]; then
  echo "Branch protection applied successfully."
  echo "Tip: run 'gh pr checks <pr-number>' to confirm required check names are correct."
  exit 0
fi

echo "Branch protection was NOT fully applied."
exit 1
