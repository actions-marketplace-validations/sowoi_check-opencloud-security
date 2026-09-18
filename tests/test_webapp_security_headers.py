"""
The security headers on every kind of response, not only the landing page.

``test_webapp_api.py`` proves the landing page carries the policy. The
middleware only *defaults* each header (``setdefault``), so a route that
sets its own - the badge, a public-cache document, an error handler - is
where a weaker policy would slip in unseen. These walk the response kinds
a stranger can reach: pages, errors, the JSON API, every export, the badge,
static files, redirects and the operator's area.
"""

from __future__ import annotations

import asyncio
import re

import pytest

from tests.fake_opencloud import FakeOpenCloud, InstanceBehaviour
from tests.webapp_support import (  # noqa: F401 - the fixtures are autouse
    MEMORY_URL,
    _isolated_backend,
    _offline_resolver,
    client,
    settings,
)
from webapp.redis_backend import memory_backend
from webapp.store import ScanStore
from webapp.tasks import run_scan

IDENTIFIER = "c1d2e3f4-5a6b-4c7d-8e9f-0a1b2c3d4e5f"
UNKNOWN = "0f4a1f22-7ce0-4f74-8a01-4d1d5b60e2aa"

# Placeholders only: the outpost's shared secret and the operator it vouches for.
SECRET = "b" * 48
OPERATOR = "operator"
FORWARDED = {
    "x-cos-admin-proxy": SECRET,
    "x-authentik-username": OPERATOR,
    "sec-fetch-site": "same-origin",
}

#: The headers no response may go without, whatever set the rest.
ALWAYS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
    "cross-origin-opener-policy": "same-origin",
}


@pytest.fixture
def finished():
    """One real scan of the fake instance, stored and completed under IDENTIFIER."""
    configured = settings(allow_private_targets=True, verify_tls=False, scan_timeout=5)
    store = ScanStore(backend=memory_backend(MEMORY_URL), ttl=configured.result_ttl)
    with FakeOpenCloud(InstanceBehaviour()) as instance:
        asyncio.run(
            store.create(
                IDENTIFIER,
                target=f"http://{instance.host}",
                ignore_hardenings=(),
                output_format="dashboard",
            )
        )
        asyncio.run(run_scan({"web_settings": configured, "store": store}, IDENTIFIER))
    return IDENTIFIER


def _assert_hardened(response, label: str) -> None:
    for name, value in ALWAYS.items():
        assert response.headers.get(name) == value, f"{label}: {name}"
    policy = response.headers.get("content-security-policy", "")
    assert policy, f"{label}: no content-security-policy"
    assert "unsafe-eval" not in policy, label
    assert "http:" not in policy and "https:" not in policy, f"{label}: a foreign origin in {policy}"


def _assert_scripts_only_from_self(policy: str, label: str) -> None:
    directives = dict(part.strip().split(" ", 1) for part in policy.split(";") if " " in part.strip())
    script = directives.get("script-src", directives.get("default-src", ""))
    assert "'unsafe-inline'" not in script, f"{label}: {policy}"
    assert "*" not in script, f"{label}: {policy}"
    assert "frame-ancestors 'none'" in policy, f"{label}: {policy}"


def test_every_kind_of_page_and_error_carries_the_strict_policy():
    """Pages, errors and the JSON API all answer with the headers the landing page has."""
    test_client = client()
    responses = {
        "landing page": test_client.get("/"),
        "unknown page": test_client.get("/no-such-page", headers={"accept": "text/html"}),
        "unknown JSON": test_client.get("/no-such-page", headers={"accept": "application/json"}),
        "unknown scan page": test_client.get(f"/scan/{UNKNOWN}"),
        "unknown scan API": test_client.get(f"/api/scans/{UNKNOWN}"),
        "malformed uuid": test_client.get("/api/scans/not-a-uuid"),
        "refused field": test_client.post(
            "/api/scans", json={"target_url": "https://opencloud.example.com", "workers": 64}
        ),
        "wrong method": test_client.delete("/api/scans"),
        "health": test_client.get("/healthz"),
        "openapi": test_client.get("/openapi.json"),
        "static script": test_client.get("/static/js/app.js"),
        "robots": test_client.get("/robots.txt"),
    }
    assert responses["refused field"].status_code == 422
    for label, response in responses.items():
        _assert_hardened(response, label)
        _assert_scripts_only_from_self(response.headers["content-security-policy"], label)


def test_a_permanent_redirect_is_hardened_too():
    """A 308 is a response a browser renders nothing from, but a proxy may cache - it still carries the headers."""
    response = client().get("/about/", follow_redirects=False)
    assert response.status_code in {301, 308}
    _assert_hardened(response, "redirect")


def test_everything_tied_to_a_uuid_is_never_stored_by_a_cache(finished):
    """A result is somebody's scan: no page, JSON body, export or badge for it may be kept by a cache."""
    test_client = client(allow_private_targets=True)
    paths = [
        f"/scan/{finished}",
        f"/api/scans/{finished}",
        f"/api/scans/{finished}/export/csv",
        f"/api/scans/{finished}/export/sarif",
        f"/api/scans/{finished}/export/pdf",
        f"/api/scans/{finished}/badge.svg",
        f"/scan/{UNKNOWN}",
        f"/api/scans/{UNKNOWN}",
    ]
    for path in paths:
        response = test_client.get(path)
        cache = response.headers.get("cache-control", "")
        assert "no-store" in cache, f"{path}: {cache!r}"
        assert "public" not in cache, f"{path}: {cache!r}"
        _assert_hardened(response, path)


def test_the_exports_are_downloads_not_documents(finished):
    """An export is saved, never rendered, so a crafted value in a report cannot run in this origin."""
    test_client = client(allow_private_targets=True)
    for fmt in ("csv", "sarif", "pdf"):
        response = test_client.get(f"/api/scans/{finished}/export/{fmt}")
        assert response.status_code == 200, fmt
        assert "attachment" in response.headers.get("content-disposition", ""), fmt
        assert "text/html" not in response.headers.get("content-type", ""), fmt
        _assert_scripts_only_from_self(response.headers["content-security-policy"], fmt)


def test_the_badge_is_an_svg_that_may_run_nothing(finished):
    """The badge sets its own policy; it must forbid scripts outright, not merely inherit less."""
    response = client(allow_private_targets=True).get(f"/api/scans/{finished}/badge.svg")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    policy = response.headers["content-security-policy"]
    assert "default-src 'none'" in policy
    assert "script-src" not in policy
    assert "<script" not in response.text.lower()
    assert not re.search(r"\son[a-z]+\s*=", response.text, re.IGNORECASE), "an inline event handler in the badge"
    _assert_hardened(response, "badge")


@pytest.mark.parametrize("path", ["/docs/", "/redoc/", "/docs/oauth2-redirect", "/DOCS", "/api/docs"])
def test_the_docs_relaxation_is_scoped_to_exactly_two_paths(path):
    """'unsafe-inline' styles belong to /docs and /redoc alone, never to a neighbouring address."""
    response = client(enable_docs=True).get(path, follow_redirects=False)
    policy = response.headers["content-security-policy"]
    assert "'unsafe-inline'" not in policy, f"{path} ({response.status_code}): {policy}"
    _assert_hardened(response, path)


def test_the_docs_relaxation_does_not_exist_when_the_docs_are_off():
    """With the docs off, /docs is an ordinary 404 under the strict policy."""
    test_client = client()
    for path in ("/docs", "/redoc"):
        response = test_client.get(path)
        assert response.status_code == 404
        assert "'unsafe-inline'" not in response.headers["content-security-policy"]


def test_the_operators_pages_are_hardened_and_never_cached():
    """The operator's area answers with the strict policy, keeps nothing in a cache and asks not to be indexed."""
    test_client = client(admin_enabled=True, admin_proxy_secret=SECRET, admin_users=(OPERATOR,))
    for path in ("/admin", "/admin/configuration", "/admin/rules", "/admin/state"):
        response = test_client.get(path, headers=FORWARDED)
        assert response.status_code == 200, path
        _assert_hardened(response, path)
        _assert_scripts_only_from_self(response.headers["content-security-policy"], path)
        assert "no-store" in response.headers.get("cache-control", ""), path
        assert "noindex" in response.headers.get("x-robots-tag", ""), path
    # And a stranger's request is refused exactly like any unknown address.
    for path in ("/admin", "/admin/state"):
        stranger = test_client.get(path)
        assert stranger.status_code == 404, path
        _assert_hardened(stranger, f"stranger {path}")
