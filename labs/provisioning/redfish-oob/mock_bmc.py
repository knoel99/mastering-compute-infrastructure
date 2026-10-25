#!/usr/bin/env python3
"""A SIMULATED Redfish service (standard library only) for the lab: not a real BMC, not a full implementation.

It serves four resources whose paths and property names follow the DMTF Redfish specification (service root
/redfish/v1/, Systems collection, ComputerSystem with Status.Health / HealthRollup / PowerState and the Reset action),
with synthetic values. Deliberate shortcuts: plain HTTP and one Basic-auth account. DSP0266 requires HTTPS for Basic
authentication, so never copy this transport to a real network.

Usage: mock_bmc.py [--health OK|Warning|Critical] [--port-file FILE]   (port 0 = pick a free port)
"""
import argparse
import base64
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RESET_TYPES = ["On", "ForceOff", "GracefulShutdown", "ForceRestart", "PowerCycle"]
RESET_PATH = "/redfish/v1/Systems/1/Actions/ComputerSystem.Reset"


class State:
    def __init__(self, user="admin-sim", password="not-a-real-secret", health="OK"):
        self.user, self.password, self.health = user, password, health
        self.power = "On"
        self.resets = []
        self.lock = threading.Lock()


def make_handler(state):
    class Handler(BaseHTTPRequestHandler):
        server_version = "MockBMC/0"

        def log_message(self, fmt, *args):  # keep test output quiet
            pass

        def _send(self, code, body=None):
            data = json.dumps(body).encode() if body is not None else b""
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("OData-Version", "4.0")
            self.end_headers()
            self.wfile.write(data)

        def _authorized(self):
            hdr = self.headers.get("Authorization", "")
            if not hdr.startswith("Basic "):
                return False
            try:
                user, _, pw = base64.b64decode(hdr[6:]).decode().partition(":")
            except Exception:
                return False
            return user == state.user and pw == state.password

        def _status(self):
            return {"State": "Enabled", "Health": state.health, "HealthRollup": state.health}

        def do_GET(self):
            path = self.path.rstrip("/") or "/"
            if path == "/redfish/v1":  # the service root needs no authentication
                return self._send(200, {"@odata.id": "/redfish/v1/", "Id": "RootService", "Systems": {"@odata.id": "/redfish/v1/Systems"},
                                        "Chassis": {"@odata.id": "/redfish/v1/Chassis"}})
            if not self._authorized():
                return self._send(401, {"error": {"code": "Base.1.0.NoValidSession", "message": "authentication required"}})
            if path == "/redfish/v1/Systems":
                return self._send(200, {"Members": [{"@odata.id": "/redfish/v1/Systems/1"}], "Members@odata.count": 1})
            if path == "/redfish/v1/Systems/1":
                return self._send(200, {"@odata.id": "/redfish/v1/Systems/1", "Id": "1", "Name": "sim-gpu-node", "PowerState": state.power,
                                        "Status": self._status(),
                                        "Actions": {"#ComputerSystem.Reset": {"target": RESET_PATH,
                                                                              "ResetType@Redfish.AllowableValues": RESET_TYPES}}})
            if path == "/redfish/v1/Chassis":
                return self._send(200, {"Members": [{"@odata.id": "/redfish/v1/Chassis/1"}], "Members@odata.count": 1})
            if path == "/redfish/v1/Chassis/1":
                return self._send(200, {"@odata.id": "/redfish/v1/Chassis/1", "Id": "1", "Status": self._status()})
            return self._send(404, {"error": {"code": "Base.1.0.ResourceMissingAtURI", "message": "not found"}})

        def do_POST(self):
            if not self._authorized():
                return self._send(401, {"error": {"code": "Base.1.0.NoValidSession", "message": "authentication required"}})
            if self.path.rstrip("/") != RESET_PATH:
                return self._send(404, {"error": {"code": "Base.1.0.ResourceMissingAtURI", "message": "not found"}})
            length = int(self.headers.get("Content-Length", "0"))
            try:
                req = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                return self._send(400, {"error": {"code": "Base.1.0.MalformedJSON", "message": "bad JSON"}})
            rtype = req.get("ResetType")
            if rtype not in RESET_TYPES:
                return self._send(400, {"error": {"code": "Base.1.0.PropertyValueNotInList", "message": f"ResetType {rtype!r} not allowed"}})
            with state.lock:
                state.resets.append(rtype)
                state.power = "Off" if rtype in ("ForceOff", "GracefulShutdown") else "On"
            return self._send(200, {"@Message.ExtendedInfo": [{"MessageId": "Base.1.0.Success"}]})

    return Handler


def make_server(state, port=0):
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(state))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--health", default="OK", choices=["OK", "Warning", "Critical"])
    ap.add_argument("--port-file")
    ap.add_argument("--password-file", help="file holding the Basic-auth password (default: a fixed non-secret test value)")
    a = ap.parse_args()
    password = open(a.password_file, encoding="utf-8").read().strip() if a.password_file else "not-a-real-secret"
    srv = make_server(State(password=password, health=a.health))
    if a.port_file:
        open(a.port_file, "w", encoding="utf-8").write(str(srv.server_address[1]))
    print(f"mock BMC listening on 127.0.0.1:{srv.server_address[1]}", file=sys.stderr)
    srv.serve_forever()


if __name__ == "__main__":
    main()
