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
    """TO WRITE (milestone 1). Raise ValueError whose message lists EVERY problem (the tests look for these phrases):
    * an account name that is not lower case: "Slurm lower-cases names"
    * a parent that is neither "root" nor a defined account: "unknown parent X"
    * a fairshare that is not a non-negative integer: "non-negative integer"
    * a parent cycle: "parent cycle"
    * a QOS that preempts an undefined QOS: "preempts unknown qos X"
    * a user whose account is undefined: "unknown account X"; a user QOS that is undefined: "unknown qos X"
    Return True when the configuration is valid."""
    raise NotImplementedError


def parse_state(assoc_text, qos_text):
    """TO WRITE (milestone 1). Live state from the `-nP` output of
    `sacctmgr show assoc format=Cluster,Account,User,ParentName,Share,QOS` (fixtures/assoc.txt) and
    `show qos format=Name,Priority,Preempt` (fixtures/qos.txt). Return
    {"accounts": {name: {"parent": str|None, "fairshare": int|None}},   # rows with an empty User column
     "user_accounts": {user: {accounts}}, "user_qos": {user: {qos names}},   # rows with a User
     "qos": {name: {"priority": int, "preempt": frozenset}}}"""
    raise NotImplementedError


def plan(cfg, current):
    """TO WRITE (milestone 2). The ORDERED argv lists that are missing from `current`, never a delete, in the syntax
    that was run on a real Slurm 23.11.4 (see the tests for the exact strings):
      QOS first, sorted by name:   sacctmgr -i add qos NAME Priority=N [Preempt=a,b]
                                   sacctmgr -i modify qos where name=NAME set Priority=N [Preempt=a,b]
      accounts, parents first:     sacctmgr -i add account NAME parent=P fairshare=N
                                   sacctmgr -i modify account where name=NAME set fairshare=N
      users, sorted by name:       sacctmgr -i add user NAME account=A
                                   sacctmgr -i modify user where name=NAME set qos+=Q   (not for the default 'normal')
    `sacctmgr add` exits with status 1 on something that already exists: a plan must not contain such a command."""
    raise NotImplementedError


def drift(cfg, current):
    """TO WRITE. {"accounts": [...], "qos": [...], "users": [...]} present in the live state but not in cfg
    (root excluded). Never removed automatically."""
    raise NotImplementedError


def apply(commands, run):
    """TO WRITE. Run each argv with run(argv) -> (returncode, text); stop at the first non-zero status with a
    RuntimeError that names the command; return the number of commands run."""
    raise NotImplementedError


# Provided (command line used by verify-live.sh): prints the plan, with --apply runs it. It calls the functions above.
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
