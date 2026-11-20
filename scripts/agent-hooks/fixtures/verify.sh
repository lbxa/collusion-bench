#!/usr/bin/env bash
set -euo pipefail
if [ -n "${VERIFY_EXPECT_ARG:-}" ]; then
  [ "$#" -eq 1 ] && [ "$1" = "$VERIFY_EXPECT_ARG" ] || exit 2
fi
printf 'Fixture verification output\n'
exit "${VERIFY_EXIT:-0}"
