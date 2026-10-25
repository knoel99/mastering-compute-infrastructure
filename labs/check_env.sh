#!/usr/bin/env bash
# Reports what this machine can run. Informational: it never installs anything.
#   PYTHON=/path/to/python bash labs/check_env.sh        (default: python3)
#   --strict  exit 1 when level A is not fully available
# shellcheck disable=SC2015  # "a && b || c" is intended here: ok() and no() always succeed
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

echo "level A: CPU, no root (base Python stack; each module adds the tools listed under extras)"
a_missing=0
if has "$PY"; then ok "python" "$("$PY" --version 2>&1)"; else no "python"; a_missing=1; fi
for mod in torch numpy scipy pytest yaml; do
  if v=$("$PY" -c "import $mod; print(getattr($mod,'__version__',''))" 2>/dev/null); then ok "python module $mod" "$v"; else no "python module $mod"; a_missing=1; fi
done
has git && ok git "$(git --version | cut -d' ' -f3)" || { no git; a_missing=1; }
has pandoc && ok "pandoc (only to rebuild the site)" "$(pandoc --version | head -1 | cut -d' ' -f2)" || echo "  pandoc (only to rebuild the site)   absent, optional"

echo "level B: disposable Linux machine with root (Slurm labs: module 5, project 1; promtool: module 14, projects 1 and 5)"
for t in sinfo sbatch sacctmgr munge mariadbd promtool; do
  has "$t" && ok "$t" || no "$t" "see lab-setup page"
done

echo "extras by module (informational; each module page lists its own commands)"
# tool:who-needs-it pairs; a missing extra is reported, never fatal
for pair in "stress-ng:lab 1.2" "fio:labs 1.2, 8.x" "systemd-analyze:lab 1.5" "shellcheck:modules 1, 6, 13" \
            "gcc:module 3" "mpicc:module 3" "mpirun:module 3" "dnsmasq:module 6" "terraform:lab 6.2" "ansible-playbook:module 6" \
            "curl:labs 12.4, 14.1" "openssl:labs 12.4, 14.1" "etcd:lab 16.4 (optional part)"; do
  t="${pair%%:*}"; who="${pair#*:}"
  has "$t" && ok "$t" "($who)" || no "$t" "($who)"
done
for pair in "mpi4py:module 3" "numba:module 4" "triton:module 4" "safetensors:module 10" "ray:module 11" "jsonschema:module 12" \
            "kubernetes_validate:module 12" "prometheus_client:module 14" "yamllint:module 13, project 4 (required)" "pyarrow:module 8 (optional)"; do
  mod="${pair%%:*}"; who="${pair#*:}"
  if "$PY" -c "import $mod" >/dev/null 2>&1; then ok "python module $mod" "($who)"; else no "python module $mod" "($who)"; fi
done

echo "level C: GPU (optional extensions only)"
if has nvidia-smi && nvidia-smi -L >/dev/null 2>&1; then ok "nvidia-smi" "$(nvidia-smi -L | wc -l) GPU(s)"; else echo "  GPU                                none detected (fine: nothing is required)"; fi

[ "$strict" = 1 ] && [ "$a_missing" = 1 ] && { echo "level A incomplete"; exit 1; }
exit 0
