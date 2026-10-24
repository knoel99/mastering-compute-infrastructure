#!/usr/bin/env bash
# ensure_sysctl.sh [--dry-run] [--apply] [--conf FILE] key=value [key=value ...]
#
# Idempotent: make sure each key is set to the wanted value in a sysctl drop-in file.
# Existing lines of the file (other keys, comments) are kept; a key is replaced, never duplicated.
#   --dry-run   report what would change, write nothing
#   --apply     also set the running kernel value with `sysctl -w` (needs root)
#   --conf FILE drop-in file (default /etc/sysctl.d/90-mci.conf)
#
# Exit status:  0 nothing to change   10 changed (or would change with --dry-run)
#               2 usage error         1 failure
set -euo pipefail

conf=/etc/sysctl.d/90-mci.conf
dry=0
apply=0
pairs=()

usage() { sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 2; }
log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >&2; }

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) dry=1 ;;
    --apply) apply=1 ;;
    --conf) [ $# -ge 2 ] || usage; conf="$2"; shift ;;
    -h|--help) usage ;;
    -*) echo "unknown option: $1" >&2; usage ;;
    *) pairs+=("$1") ;;
  esac
  shift
done
[ "${#pairs[@]}" -gt 0 ] || usage

# the value is later used in a sed replacement: refuse the characters that sed would interpret (| & \)
pair_re='^[a-z0-9_]+(\.[a-z0-9_-]+)+=[^[:space:]|&\\]+$'
for p in "${pairs[@]}"; do
  [[ "$p" =~ $pair_re ]] || { echo "invalid key=value: $p" >&2; exit 2; }
done

value_of() { # value configured for key $2 in file $1, nothing if the key is absent
  awk -v k="$2" -F'[[:space:]]*=[[:space:]]*' '{ sub(/^[[:space:]]+/, "") } $1 == k { v = $2 } END { if (v != "") print v }' "$1"
}

if [ "$dry" = 0 ]; then mkdir -p "$(dirname "$conf")"; fi  # before mktemp: the temporary file must sit next to $conf for mv to be atomic
tmp="$(mktemp "${conf}.XXXXXX" 2>/dev/null || mktemp)"
trap 'rm -f "$tmp"' EXIT
if [ -e "$conf" ]; then cp "$conf" "$tmp"; else : > "$tmp"; fi

changed=0
for p in "${pairs[@]}"; do
  key="${p%%=*}"; want="${p#*=}"
  have="$(value_of "$tmp" "$key")"
  if [ "$have" = "$want" ]; then
    log "unchanged: $key = $want"
    continue
  fi
  changed=1
  if [ "$dry" = 1 ]; then verb="would change"; else verb="changed"; fi
  log "$verb: $key ${have:-<unset>} -> $want"
  if grep -qE "^[[:space:]]*${key//./\\.}[[:space:]]*=" "$tmp"; then
    sed -i -E "s|^[[:space:]]*${key//./\\.}[[:space:]]*=.*|${key} = ${want}|" "$tmp"
  else
    printf '%s = %s\n' "$key" "$want" >> "$tmp"
  fi
  if [ "$apply" = 1 ] && [ "$dry" = 0 ]; then
    sysctl -w "${key}=${want}" >/dev/null
  fi
done

if [ "$dry" = 0 ] && [ "$changed" = 1 ]; then
  chmod 0644 "$tmp"
  mv "$tmp" "$conf"   # atomic replacement on the same filesystem
fi
[ "$changed" = 0 ] || exit 10
exit 0
