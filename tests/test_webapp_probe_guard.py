"""
The probe guard: a client whose scans keep finding no OpenCloud is blocked.

Every test here goes through the real submission endpoint and the real worker
job, against addresses that either are ``tests/fake_opencloud.py`` or refuse
the connection, so the block is earned the way a stranger would earn it.
"""

from __future__ import annotations

import asyncio
import socket

from tests.fake_opencloud import FakeOpenCloud
from tests.webapp_support import (  # noqa: F401 - the fixtures are autouse
    MEMORY_URL,
    _isolated_backend,
    _offline_resolver,
    backend,
    client,
    settings,
)
from webapp.redis_backend import memory_backend
from webapp.store import ScanStore, prober_key
from webapp.tasks import run_scan

PROBE_SETTINGS = {
    "allow_private_targets": True,
    "verify_tls": False,
    "scan_timeout": 2,
    "probe_limit": 5,
    "probe_window": 300,
    "probe_block": 3600,
}


def _closed_port() -> int:
    """A loopback port nothing listens on, so the scan finds no OpenCloud."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _worker(**overrides):
    configured = settings(**{**PROBE_SETTINGS, **overrides})
    store = ScanStore(backend=memory_backend(MEMORY_URL), ttl=configured.result_ttl)
    return {"web_settings": configured, "store": store}


def _scan(test_client, context, target: str):
    """Submit through the API, run the worker job, return the submission."""
    response = test_client.post("/api/scans", json={"target_url": target})
    if response.status_code == 202:
        asyncio.run(run_scan(context, response.json()["uuid"]))
    return response


def test_five_hosts_that_are_not_opencloud_block_the_client_for_an_hour():
    """
    Scanning a list of addresses to see what answers is not what this is for.

    Each of the five is accepted - the block is earned by the outcome, not
    guessed from the address - and the sixth submission is the one refused,
    with a Retry-After of the whole block. Four not blocking is its own test.
    """
    test_client = client(**PROBE_SETTINGS)
    context = _worker()

    for _ in range(5):
        assert _scan(test_client, context, f"http://127.0.0.1:{_closed_port()}").status_code == 202

    refused = test_client.post("/api/scans", json={"target_url": "http://127.0.0.1:1"})

    assert refused.status_code == 429
    assert 3500 < int(refused.headers["Retry-After"]) <= 3600
    assert refused.json()["selfHostUrl"] == "https://github.com/sowoi/check-opencloud-security"


def test_four_hosts_that_are_not_opencloud_do_not_block():
    """A handful of typos is a person, not a sweep."""
    test_client = client(**PROBE_SETTINGS)
    context = _worker()

    for _ in range(4):
        _scan(test_client, context, f"http://127.0.0.1:{_closed_port()}")

    with FakeOpenCloud() as instance:
        accepted = test_client.post("/api/scans", json={"target_url": f"http://{instance.host}"})

    assert accepted.status_code == 202


def test_the_same_host_that_is_not_opencloud_counts_every_time():
    """
    Asking one address over and over whether it answers yet is probing too.

    Counting distinct hosts only would let a client watch a single address
    for as long as it liked.
    """
    test_client = client(**PROBE_SETTINGS)
    context = _worker()
    target = f"http://127.0.0.1:{_closed_port()}"

    for _ in range(5):
        assert _scan(test_client, context, target).status_code == 202

    assert test_client.post("/api/scans", json={"target_url": target}).status_code == 429


def test_scans_that_find_opencloud_never_count_towards_a_block():
    """Somebody checking their own instance repeatedly must never be blocked."""
    test_client = client(**PROBE_SETTINGS)
    context = _worker()

    with FakeOpenCloud() as instance:
        target = f"http://{instance.host}"
        for _ in range(6):
            assert _scan(test_client, context, target).status_code == 202
        assert test_client.post("/api/scans", json={"target_url": target}).status_code == 202


def test_strikes_outside_the_window_do_not_add_up():
    """Five failures spread over a day are not a sweep, and must not be one."""
    test_client = client(**PROBE_SETTINGS)
    context = _worker()

    for _ in range(4):
        _scan(test_client, context, f"http://127.0.0.1:{_closed_port()}")
    backend().advance(301)
    _scan(test_client, context, f"http://127.0.0.1:{_closed_port()}")

    assert test_client.post("/api/scans", json={"target_url": "http://127.0.0.1:1"}).status_code == 202


def test_the_block_ends_on_its_own():
    """A block nobody lifts has to lift itself, or it is a ban by accident."""
    test_client = client(**PROBE_SETTINGS)
    context = _worker()
    for _ in range(5):
        _scan(test_client, context, f"http://127.0.0.1:{_closed_port()}")
    assert test_client.post("/api/scans", json={"target_url": "http://127.0.0.1:1"}).status_code == 429

    backend().advance(3601)

    assert test_client.post("/api/scans", json={"target_url": "http://127.0.0.1:1"}).status_code == 202


def test_a_blocked_client_does_not_spend_its_client_allowance():
    """Refusals during a block must not leave the visitor rate limited after it."""
    test_client = client(ip_rate_limit=6, ip_rate_window=7200, **PROBE_SETTINGS)
    context = _worker()
    for _ in range(5):
        _scan(test_client, context, f"http://127.0.0.1:{_closed_port()}")

    for _ in range(10):
        assert test_client.post("/api/scans", json={"target_url": "http://127.0.0.1:1"}).status_code == 429
    backend().advance(3601)

    # The client window outlasts the block, so the five submissions that
    # earned it still count: one of six is left, and it must still be there.
    assert test_client.post("/api/scans", json={"target_url": "http://127.0.0.1:1"}).status_code == 202


def test_the_guard_switched_off_never_blocks():
    """``COS_WEB_PROBE_LIMIT=0`` is an operator's way out and must mean it."""
    test_client = client(**{**PROBE_SETTINGS, "probe_limit": 0})
    context = _worker(probe_limit=0)
    target = f"http://127.0.0.1:{_closed_port()}"

    for _ in range(8):
        assert _scan(test_client, context, target).status_code == 202


def test_the_fingerprint_is_neither_returned_nor_kept_after_the_scan():
    """
    Whom a scan counts against is the service's business, not the uuid holder's.

    It must not appear in the result, and must be gone once the worker knows
    the outcome - but it has to exist while the scan waits, or nothing counts.
    """
    test_client = client(**PROBE_SETTINGS)
    context = _worker()

    submitted = test_client.post("/api/scans", json={"target_url": f"http://127.0.0.1:{_closed_port()}"})
    identifier = submitted.json()["uuid"]
    stored = asyncio.run(backend().get(prober_key(identifier)))
    assert stored

    asyncio.run(run_scan(context, identifier))
    body = test_client.get(f"/api/scans/{identifier}").text

    assert asyncio.run(backend().get(prober_key(identifier))) is None
    assert stored not in body
    assert "prober" not in body
