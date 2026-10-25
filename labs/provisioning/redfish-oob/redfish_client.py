#!/usr/bin/env python3
"""Minimal out-of-band health client: discover Systems from the service root, read Status, decide, optionally reset.

The password is read from the environment variable BMC_PASSWORD, never from the command line (a command line is visible
to every local user through the process list). A real deployment must use https:// and verify the BMC certificate.

Usage: redfish_client.py BASE_URL [--user NAME] [--reset RESETTYPE]     exit: 0 healthy, 1 drain advised, 2 error
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

ORDER = {"OK": 0, "Warning": 1, "Critical": 2}


class RedfishError(Exception):
    pass


def request(base, path, user=None, password=None, body=None):
    req = urllib.request.Request(base.rstrip("/") + path, method="POST" if body is not None else "GET")
    if user is not None:
        token = base64.b64encode(f"{user}:{password}".encode()).decode()
        req.add_header("Authorization", "Basic " + token)
    if body is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(body).encode()
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raise RedfishError(f"{exc.code} on {path}") from exc
    except urllib.error.URLError as exc:
        raise RedfishError(f"cannot reach {base}: {exc.reason}") from exc


def collect(base, user, password):
    """Follow @odata.id links from the service root: never hard-code /Systems/1, vendors differ."""
    root = request(base, "/redfish/v1/")
    out = []
    for coll_name in ("Systems", "Chassis"):
        coll = request(base, root[coll_name]["@odata.id"], user, password)
        for member in coll.get("Members", []):
            res = request(base, member["@odata.id"], user, password)
            st = res.get("Status", {})
            out.append({"id": res["@odata.id"], "kind": coll_name, "power": res.get("PowerState"),
                        "health": st.get("Health"), "rollup": st.get("HealthRollup"), "resource": res})
    return out


def verdict(items):
    """Worst HealthRollup (fallback Health) over all resources; unknown or missing values count as Warning."""
    worst = "OK"
    for it in items:
        h = it["rollup"] or it["health"]
        h = h if h in ORDER else "Warning"
        if ORDER[h] > ORDER[worst]:
            worst = h
    return worst, ("drain" if worst == "Critical" else "watch" if worst == "Warning" else "ok")


def reset(base, user, password, system, rtype):
    action = system["resource"].get("Actions", {}).get("#ComputerSystem.Reset")
    if not action:
        raise RedfishError("this system exposes no Reset action")
    allowed = action.get("ResetType@Redfish.AllowableValues", [])
    if rtype not in allowed:
        raise RedfishError(f"ResetType {rtype} not in the advertised list {allowed}")
    return request(base, action["target"], user, password, {"ResetType": rtype})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base")
    ap.add_argument("--user", default=os.environ.get("BMC_USER", "admin-sim"))
    ap.add_argument("--reset")
    a = ap.parse_args()
    password = os.environ.get("BMC_PASSWORD")
    if not password:
        print("error: set BMC_PASSWORD", file=sys.stderr)
        return 2
    try:
        items = collect(a.base, a.user, password)
        worst, action = verdict(items)
        for it in items:
            print(f"{it['id']}: power={it['power']} health={it['health']} rollup={it['rollup']}")
        print(f"worst={worst} action={action}")
        if a.reset:
            system = next(i for i in items if i["kind"] == "Systems")
            reset(a.base, a.user, password, system, a.reset)
            print(f"reset {a.reset} accepted")
    except RedfishError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0 if action == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
