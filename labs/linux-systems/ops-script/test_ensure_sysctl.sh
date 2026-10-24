#!/usr/bin/env bash
# Behavioural tests for ensure_sysctl.sh. Writes only under a temporary directory.
set -uo pipefail
cd "$(dirname "$0")" || exit 1
S=./ensure_sysctl.sh
fail=0
pass() { printf 'ok   %s\n' "$1"; }
bad()  { printf 'FAIL %s\n' "$1"; fail=1; }
check() { # name command... : the command succeeds
  local name="$1"; shift
  if "$@"; then pass "$name"; else bad "$name"; fi
}
expect_rc() { # name expected_rc command...
  local name="$1" want="$2" rc=0; shift 2
  "$@" >/dev/null 2>&1 || rc=$?
  if [ "$rc" = "$want" ]; then pass "$name (rc=$rc)"; else bad "$name: rc=$rc, expected $want"; fi
}
count_lines() { grep -c "$1" "$2" || true; }
d="$(mktemp -d)"; trap 'rm -rf "$d"' EXIT
c="$d/sub/90-mci.conf"

expect_rc "creates the file and its directory, reports a change" 10 "$S" --conf "$c" vm.swappiness=10
check "file content" grep -qx 'vm.swappiness = 10' "$c"
expect_rc "second identical run changes nothing" 0 "$S" --conf "$c" vm.swappiness=10
expect_rc "a new value is a change" 10 "$S" --conf "$c" vm.swappiness=1
check "key replaced, not duplicated" test "$(count_lines 'vm.swappiness' "$c")" = 1
check "mode 0644" test "$(stat -c %a "$c")" = 644

printf '# keep me\nvm.max_map_count = 65530\n' > "$d/other.conf"
expect_rc "adds a key to an existing file" 10 "$S" --conf "$d/other.conf" vm.swappiness=10
check "comment preserved" grep -qx '# keep me' "$d/other.conf"
check "other key preserved" grep -qx 'vm.max_map_count = 65530' "$d/other.conf"

before="$(cat "$d/other.conf")"
expect_rc "dry-run reports a change" 10 "$S" --dry-run --conf "$d/other.conf" vm.swappiness=99
check "dry-run writes nothing" test "$(cat "$d/other.conf")" = "$before"
expect_rc "dry-run does not create a file" 10 "$S" --dry-run --conf "$d/never.conf" vm.swappiness=1
check "no file created by dry-run" test ! -e "$d/never.conf"

expect_rc "rejects a malformed pair" 2 "$S" --conf "$d/x.conf" 'bad key=1'
expect_rc "rejects a key without a dot" 2 "$S" --conf "$d/x.conf" swappiness=1
expect_rc "rejects a value that sed would interpret (|)" 2 "$S" --conf "$d/x.conf" 'kernel.core_pattern=|/bin/x'
check "nothing written for a rejected pair" test ! -e "$d/x.conf"
expect_rc "requires at least one pair" 2 "$S" --conf "$d/x.conf"
expect_rc "rejects an unknown option" 2 "$S" --nope vm.swappiness=1

printf '  vm.swappiness = 10\n' > "$d/indented.conf"
expect_rc "an indented line holding the wanted value is unchanged" 0 "$S" --conf "$d/indented.conf" vm.swappiness=10
check "usage text is the header comment only" test "$("$S" 2>&1 | grep -c 'set -euo')" = 0
expect_rc "the temporary file is created next to a new target even if TMPDIR is unusable" 10 env TMPDIR=/nonexistent "$S" --conf "$d/fresh/dir/90.conf" vm.swappiness=10

if [ "$(id -u)" = 0 ] && [ -w /proc/sys/vm/swappiness ]; then
  cur="$(cat /proc/sys/vm/swappiness)"
  : > "$d/apply.conf"
  expect_rc "--apply sets the running kernel value (to the value it already has)" 10 "$S" --apply --conf "$d/apply.conf" "vm.swappiness=$cur"
  check "runtime value intact" test "$(cat /proc/sys/vm/swappiness)" = "$cur"
else
  echo "skip --apply test (needs root and a writable /proc/sys)"
fi

if [ "$fail" = 0 ]; then echo "ALL OK"; else echo "SOME TESTS FAILED"; exit 1; fi
