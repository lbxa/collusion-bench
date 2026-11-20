#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
fixture="$(mktemp -d "${TMPDIR:-/tmp}/veracity-verify-fast.XXXXXX")"
trap 'rm -rf "$fixture"' EXIT
fixture_repo="$fixture/repo with spaces"
mkdir -p "$fixture_repo/scripts/agent-hooks" "$fixture_repo/docs/decisions" "$fixture/bin"
cp "$repo_root/scripts/verify-fast.sh" "$repo_root/scripts/decision-index.py" "$fixture_repo/scripts/"
cp "$repo_root/scripts/agent-hooks/fixtures/verify.sh" "$fixture_repo/scripts/agent-hooks/example.test.sh"
python3 "$fixture_repo/scripts/decision-index.py" >/dev/null

export FORBIDDEN_COMMANDS="$fixture/forbidden"
export PATH="$fixture/bin:$PATH"
cp "$repo_root/scripts/agent-hooks/fixtures/forbidden-heavy-command.sh" "$fixture/forbidden-heavy-command"
chmod +x "$fixture/forbidden-heavy-command"
for command in cargo rustup forge anvil uv pytest docker docker-compose bun npm pip; do
  ln -s ../forbidden-heavy-command "$fixture/bin/$command"
done

bash "$fixture_repo/scripts/verify-fast.sh" > "$fixture/output"
grep -Fq 'Fixture verification output' "$fixture/output"
[ ! -e "$FORBIDDEN_COMMANDS" ]
printf 'Fast verification: fixture checks and decision index completed without heavyweight tools.\n'
