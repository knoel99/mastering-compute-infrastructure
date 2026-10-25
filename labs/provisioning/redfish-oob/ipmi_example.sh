#!/usr/bin/env bash
# IPMI over LAN with ipmitool 1.8.19: shown on the course page, shellchecked, NEVER run in the lab (no BMC).
# The password is read from IPMI_PASSWORD (-E): -P would expose it in the process list.
set -euo pipefail
: "${BMC_HOST:?set BMC_HOST}" "${BMC_USER:?set BMC_USER}" "${IPMI_PASSWORD:?set IPMI_PASSWORD}"
ipmitool -I lanplus -H "$BMC_HOST" -U "$BMC_USER" -E chassis power status
