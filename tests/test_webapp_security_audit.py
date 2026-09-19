"""Regressions for trust-boundary failures found in the repository audit."""

from __future__ import annotations

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import requests
from starlette.requests import Request

from opencloud_local_scan.scanner import ScannerSettings, _Probe
from webapp.app import cross_origin_post, cross_site_post
from webapp.redis_backend import MemoryRedis
from webapp.settings import WebSettings
from webapp.store import ScanStore


@pytest.mark.parametrize("guarded", [False, True])
@pytest.mark.parametrize("follow", [False, True])
def test_redirect_bodies_are_capped_before_requests_can_buffer_them(monkeypatch, guarded, follow):
    chunks = []

    class Body:
        def stream(self, size, decode_content):
            for _ in range(10):
                chunks.append(size)
                yield b"x" * size

        def close(self):
            pass

        def release_conn(self):
            pass

    def send(adapter, request, **kwargs):
        response = requests.Response()
        response.url = request.url
        response.request = request
        if request.url.endswith("/redirect"):
            response.status_code = 302
            response.headers["Location"] = "/final"
            response.raw = Body()
        else:
            response.status_code = 200
            response._content = b"ok"
            response._content_consumed = True  # type: ignore[attr-defined]  # private to requests
        return response

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", send)
    probe = _Probe("https://opencloud.example.com", ScannerSettings(
        max_response_bytes=64, redirect_guard=(lambda url: True) if guarded else None,
    ))
    try:
        response = probe.get("/redirect", allow_redirects=follow)
        assert response is not None
        assert response.status_code == (200 if follow else 302)
        assert sum(chunks) == 65536
        assert response.content == (b"ok" if follow else b"x" * 64)
    finally:
        probe.close()


def test_webhook_dials_only_validated_addresses_and_keeps_host(monkeypatch, tmp_path):
    from urllib3.util import connection

    import check_opencloud_security as plugin

    received = []
    dialled = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers["Content-Length"]))
            received.append(dict(self.headers))
            self.send_response(204)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connect = connection.create_connection

    def dial(address, *args, **kwargs):
        dialled.append(address[0])
        assert address[0] == "93.184.216.34"
        return connect(("127.0.0.1", server.server_port), *args, **kwargs)

    credentials = tmp_path / "netrc"
    credentials.write_text("default login fixture password secret\n")
    monkeypatch.setenv("NETRC", str(credentials))
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.example.com:3128")
    monkeypatch.setenv("NO_PROXY", "")
    monkeypatch.setattr(connection, "create_connection", dial)
    monkeypatch.setattr(plugin, "_resolve_webhook_addresses", lambda url: ("93.184.216.34",))
    try:
        assert plugin._send_webhook(plugin.ScanContext(
            host="opencloud.example.com",
            webhook_url=f"http://hooks.example.com:{server.server_port}/",
            retries=0,
        ), {"status": "CRITICAL"})
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    assert dialled == ["93.184.216.34"]
    assert received[0]["Host"] == f"hooks.example.com:{server.server_port}"
    assert "Authorization" not in received[0]


def test_jwks_outages_are_rate_limited_and_recover(monkeypatch):
    import jwt

    from webapp.mcp_auth import (
        JWKS_MISS_REFETCH_SECONDS,
        OidcTokenVerifier,
        UnknownSigningKey,
    )

    now = [1000.0]
    monkeypatch.setattr("webapp.mcp_auth.time.monotonic", lambda: now[0])
    verifier = OidcTokenVerifier(jwks_uri="https://auth.example.com/jwks", issuer="issuer")
    token = jwt.encode({}, "fixture" * 8, algorithm="HS256", headers={"kid": "missing"})

    class Keys:
        calls = 0

        def get_signing_keys(self, refresh=False):
            self.calls += 1
            raise OSError("provider unavailable")

    keys = Keys()
    with pytest.raises(OSError):
        verifier._signing_key(keys, token)
    for _ in range(19):
        with pytest.raises(UnknownSigningKey):
            verifier._signing_key(keys, token)
    assert keys.calls == 1
    now[0] += JWKS_MISS_REFETCH_SECONDS + 1
    with pytest.raises(OSError):
        verifier._signing_key(keys, token)
    assert keys.calls == 2


def test_a_jwks_fetch_in_progress_does_not_start_another(monkeypatch):
    import jwt

    from webapp.mcp_auth import OidcTokenVerifier, UnknownSigningKey

    verifier = OidcTokenVerifier(jwks_uri="https://auth.example.com/jwks", issuer="issuer")
    token = jwt.encode({}, "fixture" * 8, algorithm="HS256", headers={"kid": "missing"})
    started, release = threading.Event(), threading.Event()

    class Keys:
        calls = 0

        def get_signing_keys(self, refresh=False):
            self.calls += 1
            started.set()
            assert release.wait(5)
            raise OSError("provider unavailable")

    keys = Keys()
    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(verifier._signing_key, keys, token)
        try:
            assert started.wait(5)
            for _ in range(20):
                with pytest.raises(UnknownSigningKey):
                    verifier._signing_key(keys, token)
            assert keys.calls == 1
        finally:
            release.set()
        with pytest.raises(OSError):
            first.result()


def _unending_child(channel, arguments):
    while True:
        time.sleep(0.05)


@pytest.mark.parametrize("cancel", [False, True])
def test_scan_timeout_and_cancellation_reap_the_child(monkeypatch, cancel):
    import multiprocessing

    from webapp import scan_process

    monkeypatch.setattr(scan_process, "_execute", _unending_child)
    async def scenario():
        before = {child.pid for child in multiprocessing.active_children()}
        task = asyncio.create_task(scan_process.execute_scan_process(timeout=0.3 if not cancel else 60))
        if cancel:
            await asyncio.sleep(0.3)
            task.cancel()
        with pytest.raises(asyncio.CancelledError if cancel else asyncio.TimeoutError):
            await task
        assert {child.pid for child in multiprocessing.active_children()} <= before
    asyncio.run(scenario())


@pytest.mark.parametrize("parallel", [False, True])
def test_probes_do_not_send_netrc_credentials(tmp_path, monkeypatch, parallel):
    """Anonymous scans must not authenticate with the operator's netrc."""
    credentials = tmp_path / "netrc"
    credentials.write_text("default login audit-fixture password not-a-real-secret\n")
    monkeypatch.setenv("NETRC", str(credentials))
    sent = []

    def send(session, request, **kwargs):
        sent.append(request)
        response = requests.Response()
        response.status_code = 200
        response._content = b"{}"
        response._content_consumed = True  # type: ignore[attr-defined]  # private to requests
        return response

    monkeypatch.setattr(requests.Session, "send", send)
    probe = _Probe("https://opencloud.example.com", ScannerSettings())
    try:
        if parallel:
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(probe.get, "/status.php").result()
        else:
            probe.get("/status.php")
        probe.get("/", headers={"Authorization": "Basic ZGVtbzpkZW1v"})
    finally:
        probe.close()
    assert "Authorization" not in sent[0].headers
    assert sent[1].headers["Authorization"] == "Basic ZGVtbzpkZW1v"


def test_pinned_scans_ignore_environment_proxies(monkeypatch):
    """A proxy would resolve the hostname itself and bypass the validated pin."""
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.example.com:3128")
    monkeypatch.setenv("NO_PROXY", "")
    probe = _Probe(
        "https://opencloud.example.com",
        ScannerSettings(pinned_addresses=(("opencloud.example.com", ("192.0.2.10",)),)),
    )
    try:
        options = probe.session.merge_environment_settings(
            probe.base_url, {}, True, True, None,
        )
        assert not options["proxies"]
    finally:
        probe.close()


@pytest.mark.parametrize("origin", ["null", "http://scan.example.com", "https://["])
def test_browser_origin_fallback_rejects_opaque_wrong_scheme_and_malformed_origins(origin):
    """Without Fetch Metadata, Origin must still identify the complete origin."""
    request = Request({
        "type": "http", "method": "POST", "scheme": "https",
        "server": ("scan.example.com", 443), "path": "/admin/exclusions",
        "root_path": "", "query_string": b"",
        "headers": [(b"host", b"scan.example.com"), (b"origin", origin.encode())],
    })
    configured = WebSettings(public_base_url="https://scan.example.com")
    assert cross_origin_post(request, configured)
    assert cross_site_post(request, configured)


@pytest.mark.parametrize("transition", ["mark_running", "mark_completed", "mark_failed"])
@pytest.mark.parametrize("erased", [True, False])
def test_workers_cannot_recreate_erased_or_expired_scans(transition, erased):
    """A worker finishing after deletion must not make the old capability live again."""
    async def scenario():
        backend = MemoryRedis()
        store = ScanStore(backend, ttl=60)
        identifier = "11111111-1111-4111-8111-111111111111"
        await store.create(
            identifier, target="https://opencloud.example.com",
            ignore_hardenings=(), output_format="json",
        )
        await store.mark_running(identifier)
        record = await store.get(identifier)
        assert record is not None and record.state == "running"
        if erased:
            assert (await store.purge_target("opencloud.example.com")).remaining == 0
        else:
            backend.advance(61)
        arguments = {
            "mark_running": (),
            "mark_completed": ({"version": "test", "rating": 5},),
            "mark_failed": ("test failure",),
        }
        await getattr(store, transition)(identifier, *arguments[transition])
        assert await store.get(identifier) is None
        assert await backend.keys_matching(f"scan:{identifier}:*") == []
    asyncio.run(scenario())


def test_completion_cannot_race_past_erasure(monkeypatch):
    async def scenario():
        backend = MemoryRedis()
        store = ScanStore(backend, ttl=60)
        identifier = "11111111-1111-4111-8111-111111111111"
        await store.create(identifier, target="https://opencloud.example.com", ignore_hardenings=(), output_format="json")
        conditional = backend.set_if_exists

        async def erase_then_write(required, values, *, ex):
            await store.purge_target("opencloud.example.com")
            return await conditional(required, values, ex=ex)

        monkeypatch.setattr(backend, "set_if_exists", erase_then_write)
        await store.mark_completed(identifier, {"rating": 5})
        assert await store.get(identifier) is None
        assert not await backend.keys_matching(f"scan:{identifier}:*")
    asyncio.run(scenario())


@pytest.mark.parametrize("origin", ["https://scan.example.com", "https://scan.example.com:443"])
@pytest.mark.parametrize("prefix", ["", "/security"])
def test_origin_fallback_accepts_the_configured_origin(origin, prefix):
    request = Request({
        "type": "http", "method": "POST", "scheme": "http",
        "server": ("internal.example.com", 8000), "path": "/admin/exclusions",
        "root_path": "", "query_string": b"",
        "headers": [(b"host", b"internal.example.com:8000"), (b"origin", origin.encode())],
    })
    assert not cross_origin_post(request, WebSettings(public_base_url=f"https://scan.example.com{prefix}"))


def test_explicit_plugin_proxy_and_ca_are_preserved():
    settings = ScannerSettings(proxy="http://proxy.example.com:3128", tls_ca_file="/fixture/ca.pem")
    probe = _Probe("https://opencloud.example.com", settings)
    try:
        assert settings.proxies == {"http": settings.proxy, "https": settings.proxy}
        assert settings.tls_verify == "/fixture/ca.pem"
        assert not probe.session.trust_env
    finally:
        probe.close()
    with pytest.raises(ValueError, match="pinned scan cannot use a proxy"):
        _Probe("https://opencloud.example.com", ScannerSettings(
            proxy=settings.proxy, pinned_addresses=(("opencloud.example.com", ("192.0.2.1",)),),
        ))


@pytest.mark.parametrize("chunks, expected", [([b"1234", b"5678"], 200), ([b"1234", b"56789"], 413)])
def test_request_body_limit_counts_chunks_before_calling_parsers(monkeypatch, chunks, expected):
    from webapp import request_limits

    monkeypatch.setattr(request_limits, "MAX_REQUEST_BYTES", 8)
    async def scenario():
        messages = [{"type": "http.request", "body": chunk, "more_body": index < len(chunks) - 1} for index, chunk in enumerate(chunks)]
        output, received = [], []

        async def receive():
            return messages.pop(0)

        async def send(message):
            output.append(message)

        async def app(scope, receive, send):
            received.append((await receive())["body"])
            await send({"type": "http.response.start", "status": 200, "headers": []})

        await request_limits.RequestBodyLimit(app)({"type": "http", "method": "POST"}, receive, send)
        assert output[0]["status"] == expected
        assert received == ([b"12345678"] if expected == 200 else [])
    asyncio.run(scenario())


def test_request_body_deadline_is_enforced(monkeypatch):
    from webapp import request_limits

    monkeypatch.setattr(request_limits, "REQUEST_BODY_SECONDS", 0.01)
    async def scenario():
        output = []

        async def receive():
            await asyncio.sleep(1)
            raise AssertionError("body deadline was not enforced")

        async def send(message):
            output.append(message)

        async def app(*args):
            raise AssertionError("parser must not be called")

        await request_limits.RequestBodyLimit(app)({"type": "http", "method": "POST"}, receive, send)
        assert output[0]["status"] == 408
    asyncio.run(scenario())
