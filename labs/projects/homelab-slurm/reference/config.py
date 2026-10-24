"""Accounting as code: desired state (cluster.yml) -> the sacctmgr commands that are MISSING from the live state.

Idempotence by DIFFERENCE: read what exists, add or modify only what differs. The lab scripts of the Slurm module
append `|| true` to every sacctmgr call; that makes them "idempotent" but also hides real failures, because
`sacctmgr add` on something that already exists exits with status 1 (observed on Slurm 23.11.4), exactly as a typo does.

Never destructive: the plan contains no delete or removal. Extra objects found in the live state are reported by
drift(), not removed.
"""
import yaml


def load(path):
    with open(path) as f:
        return yaml.safe_load(f)


def validate(cfg):
    """Raise ValueError listing every problem: dangling parents, cycles, bad numbers, unknown QOS or accounts."""
    problems = []
    accounts, qos, users = cfg.get("accounts", {}), cfg.get("qos", {}), cfg.get("users", {})
    for name, a in accounts.items():
        if name != name.lower():
            problems.append(f"account {name}: Slurm lower-cases names, write it as {name.lower()}")
        parent = a.get("parent", "root")
        if parent != "root" and parent not in accounts:
            problems.append(f"account {name}: unknown parent {parent}")
        fs = a.get("fairshare", 1)
        if not isinstance(fs, int) or isinstance(fs, bool) or fs < 0:
            problems.append(f"account {name}: fairshare must be a non-negative integer")
        seen, cur = {name}, parent
        while cur in accounts:
            if cur in seen:
                problems.append(f"account {name}: parent cycle through {cur}")
                break
            seen.add(cur)
            cur = accounts[cur].get("parent", "root")
    for name, q in qos.items():
        if not isinstance(q.get("priority", 0), int):
            problems.append(f"qos {name}: priority must be an integer")
        for target in q.get("preempt", []):
            if target not in qos:
                problems.append(f"qos {name}: preempts unknown qos {target}")
    for name, u in users.items():
        if u.get("account") not in accounts:
            problems.append(f"user {name}: unknown account {u.get('account')}")
        for q in u.get("qos", ["normal"]):
            if q not in qos:
                problems.append(f"user {name}: unknown qos {q}")
    if problems:
        raise ValueError("; ".join(problems))
    return True


def parse_state(assoc_text, qos_text, users_text=""):
    """Live state from `sacctmgr -nP show assoc format=Cluster,Account,User,ParentName,Share,QOS`,
    `show qos format=Name,Priority,Preempt` and `show user format=User,DefaultAccount`."""
    accounts, user_accounts, user_qos = {}, {}, {}
    for line in assoc_text.splitlines():
        if not line.strip():
            continue
        _cluster, account, user, parent, share, qos = (line.split("|") + [""] * 6)[:6]
        if not user:
            accounts[account] = {"parent": parent or None, "fairshare": int(share) if share else None}
        else:
            user_accounts.setdefault(user, set()).add(account)
            user_qos.setdefault(user, set()).update(q for q in qos.split(",") if q)
    qos_state = {}
    for line in qos_text.splitlines():
        if line.strip():
            name, prio, preempt = (line.split("|") + ["", ""])[:3]
            qos_state[name] = {"priority": int(prio or 0), "preempt": frozenset(p for p in preempt.split(",") if p)}
    return {"accounts": accounts, "user_accounts": user_accounts, "user_qos": user_qos, "qos": qos_state}


def _sacctmgr(*args):
    return ["sacctmgr", "-i", *args]


def plan(cfg, current):
    """Ordered argv lists: QOS first (users reference them), accounts parents-first, then users and their QOS."""
    cmds = []
    for name in sorted(cfg.get("qos", {})):
        want = cfg["qos"][name]
        prio = want.get("priority", 0)
        preempt = ",".join(sorted(want.get("preempt", [])))
        have = current["qos"].get(name)
        if have is None:
            args = ["add", "qos", name, f"Priority={prio}"] + ([f"Preempt={preempt}"] if preempt else [])
            cmds.append(_sacctmgr(*args))
        elif have["priority"] != prio or ",".join(sorted(have["preempt"])) != preempt:
            cmds.append(_sacctmgr("modify", "qos", "where", f"name={name}", "set", f"Priority={prio}",
                                  *([f"Preempt={preempt}"] if preempt else [])))
    done, pending = set(current["accounts"]) | {"root"}, dict(cfg.get("accounts", {}))
    while pending:
        ready = sorted(n for n, a in pending.items() if a.get("parent", "root") in done)
        if not ready:
            raise ValueError("accounts with an unreachable parent: " + ", ".join(sorted(pending)))
        for name in ready:
            want = pending.pop(name)
            fs, parent = want.get("fairshare", 1), want.get("parent", "root")
            have = current["accounts"].get(name)
            if have is None:
                cmds.append(_sacctmgr("add", "account", name, f"parent={parent}", f"fairshare={fs}"))
            elif have["fairshare"] != fs:
                cmds.append(_sacctmgr("modify", "account", "where", f"name={name}", "set", f"fairshare={fs}"))
            done.add(name)
    for name in sorted(cfg.get("users", {})):
        want = cfg["users"][name]
        if want["account"] not in current["user_accounts"].get(name, set()):
            cmds.append(_sacctmgr("add", "user", name, f"account={want['account']}"))
        have_qos = current["user_qos"].get(name, set())
        for q in sorted(set(want.get("qos", ["normal"])) - have_qos - ({"normal"} if name not in current["user_qos"] else set())):
            cmds.append(_sacctmgr("modify", "user", "where", f"name={name}", "set", f"qos+={q}"))
    return cmds


def drift(cfg, current):
    """Objects present in the live state but not in the desired state (never removed automatically)."""
    ignore = {"root"}
    return {"accounts": sorted(set(current["accounts"]) - set(cfg.get("accounts", {})) - ignore),
            "qos": sorted(set(current["qos"]) - set(cfg.get("qos", {}))),
            "users": sorted(set(current["user_accounts"]) - set(cfg.get("users", {})) - ignore)}


def apply(commands, run):
    """Run each command with run(argv) -> (returncode, text); stop at the first failure and say which."""
    for argv in commands:
        rc, out = run(argv)
        if rc != 0:
            raise RuntimeError(f"command failed (rc={rc}): {' '.join(argv)}\n{out}")
    return len(commands)


def _cli():
    import argparse
    import subprocess
    import sys
    ap = argparse.ArgumentParser(description="Print (default) or apply the sacctmgr commands that are missing.")
    ap.add_argument("config")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    cfg = load(a.config)
    validate(cfg)

    def run(argv):
        r = subprocess.run(argv, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def read(argv):
        rc, out = run(argv)
        if rc != 0:
            raise RuntimeError(f"{' '.join(argv)} failed: {out.strip()}")
        return out

    current = parse_state(read(["sacctmgr", "-nP", "show", "assoc", "format=Cluster,Account,User,ParentName,Share,QOS"]),
                          read(["sacctmgr", "-nP", "show", "qos", "format=Name,Priority,Preempt"]))
    cmds = plan(cfg, current)
    for c in cmds:
        print(" ".join(c))
    d = drift(cfg, current)
    if any(d.values()):
        print(f"# drift (present, not in {a.config}, not removed): {d}", file=sys.stderr)
    if a.apply:
        print(f"# applied {apply(cmds, run)} command(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_cli())
