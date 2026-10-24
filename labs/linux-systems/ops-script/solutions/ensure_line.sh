#!/usr/bin/env bash
# ensure_line.sh FILE LINE : append LINE to FILE unless an identical line is already there.
# Exit status: 0 already present, 10 added, 2 usage error, 1 failure.
set -euo pipefail
[ $# -eq 2 ] || { echo "usage: $0 FILE LINE" >&2; exit 2; }
file="$1"; line="$2"
if [ -e "$file" ] && grep -qxF -- "$line" "$file"; then
  exit 0
fi
# a file whose last line has no newline would swallow the new line: add the missing newline first
if [ -s "$file" ] && [ "$(tail -c1 "$file" | wc -l)" -eq 0 ]; then
  printf '\n' >> "$file"
fi
printf '%s\n' "$line" >> "$file"
exit 10
