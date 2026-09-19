"""The operator area's release check and the update request it writes (ADR 0070)."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from tests.test_webapp_admin import FORWARDED, _admin_settings
from tests.webapp_support import (  # noqa: F401 - the fixtures are autouse
    _isolated_backend,
    _offline_resolver,
)
from webapp import __version__, updates
from webapp.app import create_app


def _bumped(version: str) -> str:
    major, minor, patch = (int(part) for part in version.split("."))
    return f"{major}.{minor}.{patch + 1}"


def test_is_newer_compares_plain_releases_only():
    """A pre-release or an older version must never be offered as an update."""
    assert updates.is_newer("1.2.4", "1.2.3")
    assert updates.is_newer("1.10.0", "1.9.9")
    assert not updates.is_newer("1.2.3", "1.2.3")
    assert not updates.is_newer("1.2.2", "1.2.3")
    assert not updates.is_newer("2.0.0rc1", "1.2.3")
    assert not updates.is_newer(None, "1.2.3")


def test_the_overview_says_a_newer_release_exists_and_requests_it(monkeypatch, tmp_path):
    """The card names the release, the button writes one request, and PyPI is asked once."""
    newer = _bumped(__version__)
    calls = []

    def fake_fetch(package, timeout):
        calls.append(package)
        return newer

    monkeypatch.setattr(updates, "_fetch_latest", fake_fetch)
    app = create_app(_admin_settings(update_check=True, admin_update_dir=str(tmp_path)))
    with TestClient(app) as client:
        page = client.get("/admin", headers=FORWARDED)
        assert page.status_code == 200
        assert newer in page.text
        assert 'action="/admin/update"' in page.text

        answer = client.post("/admin/update", headers={**FORWARDED, "accept": "application/json"})
        assert answer.json() == {"state": "requested", "action": "update"}
        request = json.loads((tmp_path / "request").read_text())
        assert request["version"] == newer

        again = client.post("/admin/update", headers={**FORWARDED, "accept": "application/json"})
        assert again.json()["state"] == "pending"
    # Cached: one lookup however often the area is opened.
    assert calls == ["check-opencloud-security"]


def test_without_an_updater_the_area_only_reports_the_release(monkeypatch):
    """No update directory, no button: this process never updates itself."""
    monkeypatch.setattr(updates, "_fetch_latest", lambda package, timeout: _bumped(__version__))
    with TestClient(create_app(_admin_settings(update_check=True))) as client:
        page = client.get("/admin", headers=FORWARDED)
        assert 'action="/admin/update"' not in page.text
        answer = client.post("/admin/update", headers={**FORWARDED, "accept": "application/json"})
        assert answer.json()["state"] == "disabled"


def test_nothing_is_requested_when_the_running_release_is_the_newest(monkeypatch, tmp_path):
    """A request for the running version would restart the service for nothing."""
    monkeypatch.setattr(updates, "_fetch_latest", lambda package, timeout: __version__)
    app = create_app(_admin_settings(update_check=True, admin_update_dir=str(tmp_path)))
    with TestClient(app) as client:
        answer = client.post("/admin/update", headers={**FORWARDED, "accept": "application/json"})
        assert answer.json()["state"] == "current"
    assert not (tmp_path / "request").exists()


def test_the_update_route_is_absent_for_a_stranger(tmp_path):
    """Only the operator the outpost vouches for may ask for an update."""
    app = create_app(_admin_settings(admin_update_dir=str(tmp_path)))
    with TestClient(app) as client:
        assert client.post("/admin/update").status_code == 404
    assert not (tmp_path / "request").exists()
