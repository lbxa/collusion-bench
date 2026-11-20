#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# Stop hooks call this script directly. Keep these checks local and bounded.
for test_script in "$repo_root"/scripts/agent-hooks/*.test.sh "$repo_root"/.claude/hooks/*.test.sh; do
  [ -f "$test_script" ] || continue
  bash "$test_script"
done

python3 "$repo_root/scripts/decision-index.py" --check
