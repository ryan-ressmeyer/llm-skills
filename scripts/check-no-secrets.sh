#!/usr/bin/env bash
# Pre-commit hook: refuse to commit files that look like secrets.
set -euo pipefail

# Patterns that must never appear in the repo
FORBIDDEN_FILES=(
  ".env"
  ".env.local"
  "auth.json"
  "credentials.json"
  ".credentials.json"
)

# API key patterns to scan staged content for
FORBIDDEN_PATTERNS=(
  "sk-ant-[a-zA-Z0-9_-]{20,}"
  "sk-or-v1-[a-zA-Z0-9]{20,}"
  "sk-proj-[a-zA-Z0-9_-]{20,}"
)

staged=$(git diff --cached --name-only --diff-filter=AM)
if [[ -z "$staged" ]]; then
  exit 0
fi

fail=0

# Block forbidden filenames
while IFS= read -r file; do
  base=$(basename "$file")
  for forbidden in "${FORBIDDEN_FILES[@]}"; do
    if [[ "$base" == "$forbidden" ]]; then
      echo "ERROR: refusing to commit secret file: $file" >&2
      fail=1
    fi
  done
done <<< "$staged"

# Scan staged content for API key patterns
for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
  if git diff --cached | grep -E "$pattern" >/dev/null 2>&1; then
    echo "ERROR: staged content contains an API key matching pattern: $pattern" >&2
    fail=1
  fi
done

if (( fail )); then
  echo "" >&2
  echo "Commit blocked. Remove the offending files/content and try again." >&2
  exit 1
fi
