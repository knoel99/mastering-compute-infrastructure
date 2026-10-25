import os
import sys
import threading

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import mock_bmc  # noqa: E402
import redfish_client as rc  # noqa: E402


@pytest.fixture()
def bmc():
    def start(health="OK"):
        state = mock_bmc.State(health=health)
        srv = mock_bmc.make_server(state)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        return state, f"http://127.0.0.1:{srv.server_address[1]}", srv
    servers = []

    def factory(health="OK"):
        state, url, srv = start(health)
        servers.append(srv)
        return state, url
    yield factory
    for s in servers:
        s.shutdown()
        s.server_close()


def test_service_root_needs_no_authentication_but_systems_do(bmc):
    _, url = bmc()
    assert rc.request(url, "/redfish/v1/")["Id"] == "RootService"
    with pytest.raises(rc.RedfishError, match="401"):
        rc.request(url, "/redfish/v1/Systems")


def test_wrong_password_is_refused(bmc):
    _, url = bmc()
    with pytest.raises(rc.RedfishError, match="401"):
        rc.collect(url, "admin-sim", "wrong")


@pytest.mark.parametrize("health,action", [("OK", "ok"), ("Warning", "watch"), ("Critical", "drain")])
def test_verdict_follows_the_worst_health(bmc, health, action):
    state, url = bmc(health)
    items = rc.collect(url, state.user, state.password)
    assert {i["kind"] for i in items} == {"Systems", "Chassis"}
    assert rc.verdict(items)[1] == action


def test_missing_or_unknown_health_counts_as_warning():
    items = [{"rollup": None, "health": None}, {"rollup": "Surprising", "health": "OK"}]
    assert rc.verdict(items) == ("Warning", "watch")


def test_reset_uses_the_advertised_target_and_list(bmc):
    state, url = bmc()
    system = next(i for i in rc.collect(url, state.user, state.password) if i["kind"] == "Systems")
    rc.reset(url, state.user, state.password, system, "GracefulShutdown")
    assert state.resets == ["GracefulShutdown"] and state.power == "Off"
    with pytest.raises(rc.RedfishError, match="not in the advertised list"):
        rc.reset(url, state.user, state.password, system, "Nmi")
    assert state.resets == ["GracefulShutdown"]


def test_server_itself_rejects_a_value_outside_the_list(bmc):
    state, url = bmc()
    with pytest.raises(rc.RedfishError, match="400"):
        rc.request(url, mock_bmc.RESET_PATH, state.user, state.password, {"ResetType": "Nmi"})


def test_unreachable_bmc_is_an_error_not_a_crash():
    with pytest.raises(rc.RedfishError, match="cannot reach"):
        rc.request("http://127.0.0.1:9", "/redfish/v1/")
