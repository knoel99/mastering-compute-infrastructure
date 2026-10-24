#!/usr/bin/env bash
set -e
check_disk() { false; echo "  check_disk went on after a failure"; }
echo "1) function called as an if condition:"
if check_disk; then echo "  -> condition true"; fi
echo "2) the same function in a subshell on the left of ||:"
( check_disk ) || echo "  -> the subshell exited early"
echo "3) pipeline without pipefail:"
false | cat; echo "  status: $?"
set -o pipefail
echo "4) pipeline with pipefail:"
{ false | cat; } || echo "  status: $?"
