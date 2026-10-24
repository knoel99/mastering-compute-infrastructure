#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")" || exit 1
S=./ensure_line.sh
d="$(mktemp -d)"; trap 'rm -rf "$d"' EXIT
fail=0
rc_of() { local rc=0; "$@" >/dev/null 2>&1 || rc=$?; echo "$rc"; }
expect() { if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1 (got $2, want $3)"; fail=1; fi; }
f="$d/a.conf"
expect "adds to a missing file" "$(rc_of "$S" "$f" "alpha")" 10
expect "second call changes nothing" "$(rc_of "$S" "$f" "alpha")" 0
expect "adds a different line" "$(rc_of "$S" "$f" "beta")" 10
expect "one line per entry" "$(wc -l < "$f")" 2
printf 'no-newline-at-end' > "$d/b.conf"
expect "adds after a last line without newline" "$(rc_of "$S" "$d/b.conf" "gamma")" 10
expect "the previous line is intact" "$(head -1 "$d/b.conf")" "no-newline-at-end"
printf 'alpha-extended\n' > "$d/c.conf"
expect "a longer line containing the text is not a match" "$(rc_of "$S" "$d/c.conf" "alpha")" 10
expect "usage error" "$(rc_of "$S" "$f")" 2
if [ "$fail" = 0 ]; then echo "ALL OK"; else exit 1; fi
