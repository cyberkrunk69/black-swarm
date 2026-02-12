# Devtools

Developer utilities for Vivarium. Each script produces a single `.md` artifact. Output directories are gitignored.

## branch-status

Branch status, unmerged commits, PR info, and diff-stat vs base (master). Lean output (~10KB).

**Output:** `devtools/branch-status/branch-status_YYYY-MM-DD_HH-MM-SS.md`

- **One-click:** Double-click `branch-status.command` in Finder
- **CLI:** `./devtools/branch-status.sh` or `BASE_BRANCH=main ./devtools/branch-status.sh`

## repo-map

Pure structural inventory for Python/GitHub repos.

**Output:** `devtools/repo-map/repo-map_YYYY-MM-DD_HH-MM-SS.md`

- **One-click:** Double-click `repo-map.command` in Finder
- **CLI:** `./devtools/repo-map.sh`
