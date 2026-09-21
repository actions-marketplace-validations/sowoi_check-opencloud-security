"""The report's facts list: an advertised HTTP/3 listener and the upgrade path."""

from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from tests.fake_opencloud import FakeOpenCloud, InstanceBehaviour
from tests.webapp_support import (  # noqa: F401 - the fixtures are autouse
    _isolated_backend,
    _offline_resolver,
    settings,
)
from webapp.app import create_app
from webapp.catalog import _alternative_services, _upgrade_path
from webapp.tasks import run_scan

IDENTIFIER = "5b0f8a52-6c1e-4d7a-9e3b-2f4c8d1a7e60"


def _report(behaviour: InstanceBehaviour) -> str:
    configured = settings(allow_private_targets=True, verify_tls=False, scan_timeout=5)
    app = create_app(configured)
    with TestClient(app) as test_client:
        store = app.state.store
        with FakeOpenCloud(behaviour) as instance:
            asyncio.run(
                store.create(
                    IDENTIFIER,
                    target=f"http://{instance.host}",
                    ignore_hardenings=(),
                    output_format="dashboard",
                )
            )
            asyncio.run(run_scan({"web_settings": configured, "store": store}, IDENTIFIER))
        return test_client.get(f"/scan/{IDENTIFIER}").text


def test_an_advertised_http3_listener_is_on_the_report():
    """A scan of an instance sending Alt-Svc h3 names the UDP port; a bare one shows nothing."""
    quic = _report(InstanceBehaviour(extra_headers={"Alt-Svc": 'h3=":443"; ma=86400'}))
    bare = _report(InstanceBehaviour())

    assert "Advertised on UDP 443" in quic
    assert "HTTP/3" not in bare


def test_the_udp_ports_are_listed_once_in_order_and_tcp_entries_are_left_out():
    """Only UDP entries with a port count, each port once."""
    services = {
        "http3": True,
        "entries": [
            {"protocol": "h3", "port": 8443, "udp": True},
            {"protocol": "h3", "port": 443, "udp": True},
            {"protocol": "h3-29", "port": 443, "udp": True},
            {"protocol": "h2", "port": 9443, "udp": False},
            {"protocol": "h3", "port": None, "udp": True},
        ],
    }

    assert _alternative_services({"alternativeServices": services}) == {
        "http3": True,
        "ports": "443, 8443",
    }
    assert _alternative_services({"alternativeServices": {"http3": False}}) == {}
    assert _alternative_services({}) == {}


def test_the_upgrade_path_is_summarised_for_the_report():
    """The target, what it leaves open and the release that clears everything."""
    partial = {"upgradePath": {"target": "7.2.4", "fixes": ["A"],
                               "stillAffected": ["B", "C"], "safeVersion": "7.3.0"}}
    complete = {"upgradePath": {"target": "7.3.0", "fixes": ["A"],
                                "stillAffected": [], "safeVersion": "7.3.0"}}

    assert _upgrade_path(partial) == {"target": "7.2.4", "open": "B, C", "safe": "7.3.0"}
    assert _upgrade_path(complete) == {"target": "7.3.0", "open": "", "safe": "7.3.0"}
    assert _upgrade_path({"upgradePath": None}) == {}
    assert _upgrade_path({}) == {}
