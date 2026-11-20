#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "${0##*/}" >> "$FORBIDDEN_COMMANDS"
exit 98
