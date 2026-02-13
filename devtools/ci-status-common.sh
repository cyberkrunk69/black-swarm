#!/usr/bin/env bash
# ci-status-common.sh — Shared logic for ci-status-dry-run and ci-status-execute
# Sourced by both scripts. Do not run directly.

# Requires: REPO_ROOT, LOG_FILE (for ensure_python_deps)
# Ensures: ensure_python_deps, archive_ci_status_files

ensure_python_deps() {
  local log_file="$1"
  shift
  local modules=("$@")
  echo "--- Dependencies ---" >> "$log_file"
  for mod in "${modules[@]}"; do
    if python3 -c "import ${mod}" 2>/dev/null; then
      echo "  ${mod}: already present" >> "$log_file"
    else
      echo "  ${mod}: installing..." >> "$log_file"
      if ! python3 -m pip install "$mod" -q 2>>"$log_file"; then
        echo "  ${mod}: install failed" >> "$log_file"
        echo "--- End Dependencies ---" >> "$log_file"
        return 1
      fi
      echo "  ${mod}: installed successfully" >> "$log_file"
    fi
  done
  echo "--- End Dependencies ---" >> "$log_file"
  return 0
}

# Archive existing ci-status output files before generating new ones.
# Sets ARCHIVE_TIMESTAMP and archived_count.
archive_ci_status_files() {
  local out_dir="$1"
  local archive_dir="${out_dir}/archive"
  ARCHIVE_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  archived_count=0
  if [[ -d "$out_dir" ]]; then
    for f in "$out_dir"/ci-status_*.md "$out_dir"/ci-status_*.log; do
      [[ -f "$f" ]] || continue
      base=$(basename "$f")
      ext="${base##*.}"
      stem="${base%.*}"
      mkdir -p "$archive_dir"
      dest="$archive_dir/${stem}_archived_${ARCHIVE_TIMESTAMP}.${ext}"
      if mv "$f" "$dest" 2>/dev/null; then
        ((archived_count++)) || true
      fi
    done
  fi
}
