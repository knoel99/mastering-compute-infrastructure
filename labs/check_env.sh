#!/usr/bin/env bash
# Reports what this machine can run. Informational: it never installs anything.
#   PYTHON=/path/to/python bash labs/check_env.sh        (default: python3)
#   --strict  exit 1 when level A is not fully available
set -u
PY="${PYTHON:-python3}"
strict=0; [ "${1:-}" = "--strict" ] && strict=1
ok()  { printf '  %-34s ok   %s\n' "$1" "${2:-}"; }
no()  { printf '  %-34s MISSING  %s\n' "$1" "${2:-}"; }
has() { command -v "$1" >/dev/null 2>&1; }

echo "machine"
printf '  %-34s %s\n' "kernel" "$(uname -sr)"
printf '  %-34s %s\n' "logical CPUs" "$(nproc)"
printf '  %-34s %s\n' "memory (MiB)" "$(free -m 2>/dev/null | awk '/^Mem:/{print $2}')"
printf '  %-34s %s\n' "free disk here (GiB)" "$(df -Pk . | awk 'NR==2{printf "%.0f", $4/1048576}')"
printf '  %-34s %s\n' "root or sudo" "$([ "$(id -u)" = 0 ] && echo root || (sudo -n true 2>/dev/null && echo sudo || echo no))"

echo "level A: CPU, no root (modules 2 and 3, projects 2, 3, 4, 6)"
a_missing=0
if has "$PY"; then ok "python" "$("$PY" --version 2>&1)"; else no "python"; a_missing=1; fi
for mod in torch numpy scipy pytest yaml; do
  if v=$("$PY" -c "import $mod; print(getattr($mod,'__version__',''))" 2>/dev/null); then ok "python module $mod" "$v"; else no "python module $mod"; a_missing=1; fi
done
has git && ok git "$(git --version | cut -d' ' -f3)" || { no git; a_missing=1; }
has pandoc && ok "pandoc (only to rebuild the site)" "$(pandoc --version | head -1 | cut -d' ' -f2)" || echo "  pandoc (only to rebuild the site)   absent, optional"

echo "level B: disposable Linux machine with root (Slurm labs, project 5 promtool)"
for t in sinfo sbatch sacctmgr munge mariadbd promtool; do
  has "$t" && ok "$t" || no "$t" "see lab-setup page"
done

echo "level C: GPU (optional extensions only)"
if has nvidia-smi && nvidia-smi -L >/dev/null 2>&1; then ok "nvidia-smi" "$(nvidia-smi -L | wc -l) GPU(s)"; else echo "  GPU                                none detected (fine: nothing is required)"; fi

[ "$strict" = 1 ] && [ "$a_missing" = 1 ] && { echo "level A incomplete"; exit 1; }
exit 0
