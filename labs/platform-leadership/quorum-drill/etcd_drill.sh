#!/usr/bin/env bash
# Optional part of lab 16.4: a restore drill on a throw-away three-member etcd cluster on 127.0.0.1.
#   1. write 100 keys, take a snapshot from a live member (etcdctl snapshot save), read its status (etcdutl);
#   2. write one more key AFTER the snapshot;
#   3. stop one member: writes are still accepted (quorum 2 of 3);
#   4. stop a second member: writes are refused (no quorum);
#   5. restore the snapshot into a new data directory (etcdutl snapshot restore), start one member from it,
#      and check that the 100 keys are back and that the key written after the snapshot is lost.
# Needs etcd, etcdctl and etcdutl (v3.5 or later) in $ETCD_BIN or on PATH. Everything lives in a temporary
# directory that is removed at exit. The durations printed are measurements on your machine, not assertions.
set -euo pipefail

BIN="${ETCD_BIN:-}"
find_tool() {  # absolute path of a tool, from $ETCD_BIN first, then PATH
  if [ -n "$BIN" ] && [ -x "$BIN/$1" ]; then echo "$BIN/$1"; return 0; fi
  command -v "$1" 2>/dev/null || { echo "$1 not found: set ETCD_BIN to a directory holding etcd, etcdctl and etcdutl (v3.5 or later)" >&2; return 2; }
}
ETCD="$(find_tool etcd)"
ETCDCTL="$(find_tool etcdctl)"
ETCDUTL="$(find_tool etcdutl)"
etcdctl_cmd() { "$ETCDCTL" "$@"; }
etcdutl_cmd() { "$ETCDUTL" "$@"; }

BASE="${DRILL_PORT_BASE:-23790}"
HOST=127.0.0.1
WORK="$(mktemp -d)"
declare -a PIDS=()
cleanup() {
  for pid in "${PIDS[@]}"; do kill "$pid" 2>/dev/null || true; done
  wait 2>/dev/null || true
  rm -rf "$WORK"
}
trap cleanup EXIT

client() { echo "http://$HOST:$((BASE + $1))"; }
peer()   { echo "http://$HOST:$((BASE + 10 + $1))"; }
CLUSTER="m1=$(peer 1),m2=$(peer 2),m3=$(peer 3)"
ALL="$(client 1),$(client 2),$(client 3)"

start_member() {  # start_member <index> <data-dir> <name> <initial-cluster> <state>
  "$ETCD" --name "$3" --data-dir "$2" \
    --listen-client-urls "$(client "$1")" --advertise-client-urls "$(client "$1")" \
    --listen-peer-urls "$(peer "$1")" --initial-advertise-peer-urls "$(peer "$1")" \
    --initial-cluster "$4" --initial-cluster-state "$5" --initial-cluster-token drill \
    >"$WORK/$3.log" 2>&1 &
  PIDS[$1]=$!   # the PID of etcd itself (a backgrounded shell function would give a subshell PID)
}

wait_healthy() {  # wait_healthy <endpoints>; polls, gives up after 300 attempts
  for _ in $(seq 1 300); do
    if etcdctl_cmd --endpoints="$1" --command-timeout=1s endpoint health >/dev/null 2>&1; then return 0; fi
    sleep 0.1
  done
  echo "cluster not healthy; last log lines:" >&2
  tail -n 5 "$WORK"/*.log >&2
  return 1
}

stop_member() { kill "${PIDS[$1]}"; wait "${PIDS[$1]}" 2>/dev/null || true; unset "PIDS[$1]"; }

for i in 1 2 3 4; do  # refuse to talk to a cluster that is not ours
  if etcdctl_cmd --endpoints="$(client "$i")" --command-timeout=1s endpoint health >/dev/null 2>&1; then
    echo "port $((BASE + i)) already answers as etcd: stop it or set DRILL_PORT_BASE" >&2
    exit 2
  fi
done
echo "== etcd $("$ETCD" --version | head -n 1 | awk '{print $3}'), three members on $HOST"
for i in 1 2 3; do start_member "$i" "$WORK/m$i" "m$i" "$CLUSTER" new; done
wait_healthy "$ALL"
etcdctl_cmd --endpoints="$ALL" member list -w table

echo "== 1. write 100 keys, snapshot a live member"
for i in $(seq -w 1 100); do etcdctl_cmd --endpoints="$ALL" put "/drill/job/$i" "state-$i" >/dev/null; done
etcdctl_cmd --endpoints="$(client 1)" snapshot save "$WORK/snapshot.db" 2>"$WORK/snapshot.log" | sed "s#$WORK#\$WORK#"
etcdutl_cmd snapshot status "$WORK/snapshot.db" -w table

echo "== 2. write one key after the snapshot"
etcdctl_cmd --endpoints="$ALL" put /drill/after-snapshot written-after-backup

echo "== 3. stop m3: quorum is 2 of 3"
stop_member 3
etcdctl_cmd --endpoints="$ALL" --command-timeout=2s endpoint health -w table 2>/dev/null || true
etcdctl_cmd --endpoints="$(client 1),$(client 2)" --command-timeout=5s put /drill/one-down accepted
echo "write with one member down: accepted"

echo "== 4. stop m2: one member left, no quorum"
stop_member 2
if etcdctl_cmd --endpoints="$(client 1)" --command-timeout=2s put /drill/two-down refused 2>"$WORK/put.err"; then
  echo "unexpected: a write was accepted without quorum" >&2
  exit 1
fi
echo "write with two members down: refused ($(tail -n 1 "$WORK/put.err"))"
stop_member 1

echo "== 5. restore the snapshot into a new data directory and start one member from it"
t0=$(date +%s.%N)
etcdutl_cmd snapshot restore "$WORK/snapshot.db" --data-dir "$WORK/restored" --name r1 \
  --initial-cluster "r1=$(peer 4)" --initial-advertise-peer-urls "$(peer 4)" --initial-cluster-token restored \
  >"$WORK/restore.log" 2>&1
start_member 4 "$WORK/restored" r1 "r1=$(peer 4)" existing
wait_healthy "$(client 4)"
t1=$(date +%s.%N)
keys=$(etcdctl_cmd --endpoints="$(client 4)" get /drill/job/ --prefix --keys-only | grep -c .)
after=$(etcdctl_cmd --endpoints="$(client 4)" get /drill/after-snapshot --print-value-only)
echo "keys under /drill/job/ after restore: $keys"
echo "key written after the snapshot: ${after:-<absent>}"
awk -v a="$t0" -v b="$t1" 'BEGIN { printf "restore and restart of one member: %.1f s (measured on this machine)\n", b - a }'
[ "$keys" -eq 100 ] || { echo "expected 100 keys after restore" >&2; exit 1; }
[ -z "$after" ] || { echo "the key written after the snapshot should be lost" >&2; exit 1; }
echo "RESTORE DRILL OK"
