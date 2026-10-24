#!/usr/bin/env bash
# Shared helpers for the mini-control-plane lab. Source it; do not execute it.
# Brings up a REAL Kubernetes control plane (etcd, kube-apiserver, kube-controller-manager,
# kube-scheduler) on one machine, WITHOUT kubelets: nodes are fake objects that we create and
# whose capacity we declare. Pods are scheduled (bound to a node) but never run.
# Tested on Linux x86_64 only; needs outbound HTTPS to dl.k8s.io and registry.k8s.io.

K8S_VERSION="${K8S_VERSION:-v1.37.1}"          # read on https://dl.k8s.io/release/stable.txt on 2026-10-24
ETCD_IMAGE_REPO="etcd"                          # registry.k8s.io/etcd:3.7.0-0 = tag given by `kubeadm config images list` for v1.37.1
ETCD_AMD64_MANIFEST="sha256:1f445fa5dd06b08f3c0cf9f46e2891e9bc66cbf7e0b9c66627c40658edf4bc98"
CACHE="${K8S_MINI_CACHE:-$HOME/.cache/mci-k8s-mini}"
RUN="${K8S_MINI_RUN:-$CACHE/run}"
BIN="$CACHE/bin/$K8S_VERSION"
API_PORT="${K8S_MINI_API_PORT:-16443}"
ETCD_PORT="${K8S_MINI_ETCD_PORT:-12379}"
ETCD_PEER_PORT="${K8S_MINI_ETCD_PEER_PORT:-12380}"
FEATURE_GATES="${K8S_MINI_FEATURE_GATES:-GenericWorkload=true,WorkloadWithJob=true}"
export KUBECONFIG="$RUN/kubeconfig"

log() { printf '[mini-cp] %s\n' "$*" >&2; }

fetch_binaries() {
  mkdir -p "$BIN"
  local b want got
  for b in kube-apiserver kube-controller-manager kube-scheduler kubectl; do
    if [ ! -x "$BIN/$b" ]; then
      log "downloading $b $K8S_VERSION"
      curl -fsSL --retry 3 -o "$BIN/$b.part" "https://dl.k8s.io/release/$K8S_VERSION/bin/linux/amd64/$b"
      want="$(curl -fsSL "https://dl.k8s.io/release/$K8S_VERSION/bin/linux/amd64/$b.sha256")"
      got="$(sha256sum "$BIN/$b.part" | cut -d' ' -f1)"
      [ "$want" = "$got" ] || { log "sha256 mismatch for $b"; rm -f "$BIN/$b.part"; return 1; }
      chmod +x "$BIN/$b.part"; mv "$BIN/$b.part" "$BIN/$b"
    fi
  done
  if [ ! -x "$BIN/etcd" ]; then
    log "fetching etcd from registry.k8s.io/$ETCD_IMAGE_REPO (manifest and layers verified against their digests)"
    local tmp digest; tmp="$(mktemp -d)"
    curl -fsSL -H 'Accept: application/vnd.docker.distribution.manifest.v2+json' \
      "https://registry.k8s.io/v2/$ETCD_IMAGE_REPO/manifests/$ETCD_AMD64_MANIFEST" -o "$tmp/manifest.json"
    [ "sha256:$(sha256sum "$tmp/manifest.json" | cut -d' ' -f1)" = "$ETCD_AMD64_MANIFEST" ] || { log "manifest digest mismatch"; return 1; }
    for digest in $(python3 -c 'import json,sys; print(" ".join(l["digest"] for l in json.load(open(sys.argv[1]))["layers"] if l["size"]>1000000))' "$tmp/manifest.json"); do
      curl -fsSL "https://registry.k8s.io/v2/$ETCD_IMAGE_REPO/blobs/$digest" -o "$tmp/layer.tgz"
      [ "sha256:$(sha256sum "$tmp/layer.tgz" | cut -d' ' -f1)" = "$digest" ] || { log "layer digest mismatch"; return 1; }
      tar xzf "$tmp/layer.tgz" -C "$tmp" --wildcards 'usr/local/bin/etcd' 2>/dev/null || true
    done
    [ -x "$tmp/usr/local/bin/etcd" ] || { log "etcd binary not found in image layers"; return 1; }
    cp "$tmp/usr/local/bin/etcd" "$BIN/etcd"; rm -rf "$tmp"
  fi
}

kc() { "$BIN/kubectl" --request-timeout=30s "$@"; }

# wait_for SECONDS DESCRIPTION COMMAND... : polls a condition; the lab never asserts on elapsed time
wait_for() {
  local limit="$1" what="$2"; shift 2
  for _ in $(seq 1 "$limit"); do
    if "$@" >/dev/null 2>&1; then return 0; fi
    sleep 1
  done
  log "timeout waiting for: $what"; return 1
}

cp_down() {
  local n i alive
  for n in kube-scheduler kube-controller kube-apiserver etcd; do pkill -x "$n" 2>/dev/null || true; done
  for i in $(seq 1 40); do      # the apiserver drains connections before exiting: wait for the real exit
    alive=0
    for n in kube-scheduler kube-controller kube-apiserver etcd; do pgrep -x "$n" >/dev/null && alive=1; done
    [ "$alive" = 0 ] && return 0
    [ "$i" -ge 30 ] && for n in kube-scheduler kube-controller kube-apiserver etcd; do pkill -KILL -x "$n" 2>/dev/null || true; done
    sleep 1
  done
}

cp_up() {
  fetch_binaries
  cp_down
  rm -rf "$RUN"; mkdir -p "$RUN/etcd" "$RUN/certs"
  ADMIN_TOKEN="$(openssl rand -hex 16)"   # throwaway credential of this local cluster, regenerated at every start
  printf '%s,admin,admin,"system:masters"\n' "$ADMIN_TOKEN" > "$RUN/tokens.csv"
  openssl genrsa -out "$RUN/sa.key" 2048 2>/dev/null
  openssl rsa -in "$RUN/sa.key" -pubout -out "$RUN/sa.pub" 2>/dev/null
  setsid nohup "$BIN/etcd" --data-dir "$RUN/etcd" \
    --listen-client-urls "http://127.0.0.1:$ETCD_PORT" --advertise-client-urls "http://127.0.0.1:$ETCD_PORT" \
    --listen-peer-urls "http://127.0.0.1:$ETCD_PEER_PORT" >"$RUN/etcd.log" 2>&1 </dev/null &
    disown
  sleep 2
  setsid nohup "$BIN/kube-apiserver" --etcd-servers="http://127.0.0.1:$ETCD_PORT" \
    --service-account-issuer=https://kubernetes.default.svc \
    --service-account-key-file="$RUN/sa.pub" --service-account-signing-key-file="$RUN/sa.key" \
    --cert-dir="$RUN/certs" --secure-port="$API_PORT" --bind-address=127.0.0.1 \
    --authorization-mode=RBAC --token-auth-file="$RUN/tokens.csv" \
    --service-cluster-ip-range=10.96.0.0/16 --feature-gates="$FEATURE_GATES" \
    --runtime-config=scheduling.k8s.io/v1beta1=true >"$RUN/apiserver.log" 2>&1 </dev/null &
    disown
  wait_for 90 "apiserver certificate" test -f "$RUN/certs/apiserver.crt"
  cat > "$RUN/kubeconfig" <<KUBECONFIG_EOF
apiVersion: v1
kind: Config
clusters:
- cluster: {server: "https://127.0.0.1:$API_PORT", certificate-authority: "$RUN/certs/apiserver.crt"}
  name: mini
contexts:
- context: {cluster: mini, user: admin}
  name: mini
current-context: mini
users:
- name: admin
  user: {token: "$ADMIN_TOKEN"}
KUBECONFIG_EOF
  wait_for 90 "apiserver /readyz" kc get --raw /readyz
  # node-lifecycle-controller disabled: there is no kubelet to send heartbeats, it would taint every node
  setsid nohup "$BIN/kube-controller-manager" --kubeconfig="$RUN/kubeconfig" \
    --service-account-private-key-file="$RUN/sa.key" --controllers='*,-node-lifecycle-controller' \
    --feature-gates="$FEATURE_GATES" >"$RUN/kcm.log" 2>&1 </dev/null &
    disown
  setsid nohup "$BIN/kube-scheduler" --kubeconfig="$RUN/kubeconfig" \
    --feature-gates="$FEATURE_GATES" >"$RUN/scheduler.log" 2>&1 </dev/null &
    disown
  wait_for 60 "default service account" kc -n default get serviceaccount default
  log "control plane $K8S_VERSION up (api 127.0.0.1:$API_PORT)"
}

# add_node NAME RACK GPUS : a fake node with GPUs, labelled like a GPU Feature Discovery + topology setup
add_node() {
  local name="$1" rack="$2" gpus="${3:-8}"
  kc create -f - >/dev/null <<NODE_EOF
apiVersion: v1
kind: Node
metadata:
  name: $name
  labels:
    topology.example.com/rack: $rack
    nvidia.com/gpu.product: NVIDIA-H100-80GB-HBM3
NODE_EOF
  kc patch node "$name" --subresource=status --type=merge -p \
    "{\"status\":{\"capacity\":{\"cpu\":\"64\",\"memory\":\"512Gi\",\"pods\":\"110\",\"nvidia.com/gpu\":\"$gpus\"},\"allocatable\":{\"cpu\":\"64\",\"memory\":\"512Gi\",\"pods\":\"110\",\"nvidia.com/gpu\":\"$gpus\"},\"conditions\":[{\"type\":\"Ready\",\"status\":\"True\",\"reason\":\"FakeKubelet\",\"lastHeartbeatTime\":\"2026-01-01T00:00:00Z\",\"lastTransitionTime\":\"2026-01-01T00:00:00Z\"}]}}" >/dev/null
  # the TaintNodesByCondition admission plugin adds not-ready:NoSchedule at creation; no node controller removes it here
  kc taint nodes "$name" node.kubernetes.io/not-ready:NoSchedule- >/dev/null 2>&1 || true
}

# bound_count JOBNAME : number of pods of the job that the scheduler has bound to a node
bound_count() {
  kc get pods -l "job-name=$1" -o jsonpath='{range .items[*]}{.spec.nodeName}{"\n"}{end}' | grep -c . || true
}

# stable_bound JOBNAME N : the number of bound pods equals N and stays N for 5 consecutive polls
stable_bound() {
  local job="$1" want="$2" ok=0
  for _ in $(seq 1 90); do
    if [ "$(bound_count "$job")" = "$want" ]; then ok=$((ok+1)); else ok=0; fi
    [ "$ok" -ge 5 ] && return 0
    sleep 1
  done
  return 1
}

# reset_state : remove every job, pod, node and scheduling group so that a scenario starts from an empty cluster
reset_state() {
  kc delete job --all --cascade=background --wait=false >/dev/null 2>&1 || true
  kc delete pods --all --force --grace-period=0 >/dev/null 2>&1 || true
  kc delete workloads.scheduling.k8s.io --all >/dev/null 2>&1 || true
  kc delete podgroups.scheduling.k8s.io --all >/dev/null 2>&1 || true
  kc delete nodes --all >/dev/null 2>&1 || true
}

# start_scheduler [binpack] : (re)start kube-scheduler; with "binpack" NodeResourcesFit scores with MostAllocated
# (GPUs weigh 3, cpu and memory 1), otherwise the default LeastAllocated strategy applies.
start_scheduler() {
  local mode="${1:-default}"
  pkill -x kube-scheduler 2>/dev/null || true
  for _ in $(seq 1 20); do pgrep -x kube-scheduler >/dev/null || break; sleep 1; done
  if [ "$mode" = binpack ]; then
    cat > "$RUN/scheduler-config.yaml" <<SCHED_EOF
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
clientConnection:
  kubeconfig: $RUN/kubeconfig
profiles:
  - schedulerName: default-scheduler
    pluginConfig:
      - name: NodeResourcesFit
        args:
          scoringStrategy:
            type: MostAllocated
            resources:
              - {name: nvidia.com/gpu, weight: 3}
              - {name: cpu, weight: 1}
              - {name: memory, weight: 1}
SCHED_EOF
    setsid nohup "$BIN/kube-scheduler" --config="$RUN/scheduler-config.yaml" --feature-gates="$FEATURE_GATES" \
      >"$RUN/scheduler.log" 2>&1 </dev/null &
      disown
  else
    setsid nohup "$BIN/kube-scheduler" --kubeconfig="$RUN/kubeconfig" --feature-gates="$FEATURE_GATES" \
      >"$RUN/scheduler.log" 2>&1 </dev/null &
      disown
  fi
  sleep 3
}
