#!/usr/bin/env bash
# Install local git hooks from the repository's git_hooks directory.
HOOK_DIR="$(git rev-parse --show-toplevel)/git_hooks"
GIT_HOOKS_DIR="$(git rev-parse --git-dir)/hooks"

for hook in "$HOOK_DIR"/*; do
    hook_name=$(basename "$hook")
    ln -sf "$hook" "$GIT_HOOKS_DIR/$hook_name"
    echo "Installed $hook_name hook."
done
chmod +x scripts/install_git_hooks.sh