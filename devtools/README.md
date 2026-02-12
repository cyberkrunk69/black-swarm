# Devtools

Developer utilities for Vivarium. Each script produces a single `.md` artifact. Output directories are gitignored.

## branch-status.sh

Branch status, unmerged commits, PR info, and diff-stat vs base (master). Lean output (~10KB).

**Output:** `devtools/branch-status/branch-status_YYYYMMDD_HHMMSS.md`

```bash
./devtools/branch-status.sh
BASE_BRANCH=main ./devtools/branch-status.sh
```

## repo-map.sh

Pure structural inventory for Python/GitHub repos.

**Output:** `devtools/repo-map/repo-map_YYYYMMDD_HHMMSS.md`

```bash
./devtools/repo-map.sh
```
