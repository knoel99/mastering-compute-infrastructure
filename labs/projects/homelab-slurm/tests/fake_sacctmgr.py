"""A tiny in-memory sacctmgr that understands the commands config.plan emits and fails (rc=1) like the real one
when asked to add something that already exists or to reference something unknown (observed on Slurm 23.11.4)."""
import copy


class FakeSacctmgr:
    def __init__(self, state):
        self.state = copy.deepcopy(state)
        self.calls = []

    def run(self, argv):
        self.calls.append(argv)
        a = [x for x in argv[1:] if x != "-i"]
        st = self.state
        kv = lambda items: dict(i.split("=", 1) for i in items if "=" in i)
        if a[:2] == ["add", "account"]:
            name, opts = a[2], kv(a[3:])
            if name in st["accounts"] or opts["parent"] not in st["accounts"]:
                return 1, "Already existing account or unknown parent"
            st["accounts"][name] = {"parent": opts["parent"], "fairshare": int(opts["fairshare"])}
            return 0, ""
        if a[:2] == ["modify", "account"]:
            name = a[3].split("=", 1)[1]
            if name not in st["accounts"]:
                return 1, "unknown account"
            st["accounts"][name]["fairshare"] = int(kv(a[5:])["fairshare"])
            return 0, ""
        if a[:2] == ["add", "user"]:
            name, opts = a[2], kv(a[3:])
            if opts["account"] not in st["accounts"]:
                return 1, "unknown account"
            if opts["account"] in st["user_accounts"].get(name, set()):
                return 1, "Already existing"
            st["user_accounts"].setdefault(name, set()).add(opts["account"])
            st["user_qos"].setdefault(name, set()).add("normal")
            return 0, ""
        if a[:2] == ["add", "qos"]:
            name, opts = a[2], kv(a[3:])
            if name in st["qos"]:
                return 1, "Nothing new added."
            st["qos"][name] = {"priority": int(opts["Priority"]),
                               "preempt": frozenset(p for p in opts.get("Preempt", "").split(",") if p)}
            return 0, ""
        if a[:2] == ["modify", "qos"]:
            name, opts = a[3].split("=", 1)[1], kv(a[5:])
            if name not in st["qos"]:
                return 1, "unknown qos"
            st["qos"][name] = {"priority": int(opts["Priority"]),
                               "preempt": frozenset(p for p in opts.get("Preempt", "").split(",") if p)}
            return 0, ""
        if a[:2] == ["modify", "user"]:
            name, change = a[3].split("=", 1)[1], a[5]
            qos = change.split("+=", 1)[1]
            if name not in st["user_qos"] or qos not in st["qos"]:
                return 1, "unknown user or qos"
            st["user_qos"][name].add(qos)
            return 0, ""
        return 1, f"unsupported command {argv}"
