"""The operator area's release check and the attested, in-place update (ADR 0070)."""

from __future__ import annotations

import asyncio
import io
import tarfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from opencloud_local_scan import data_signing
from tests.test_webapp_admin import FORWARDED, _admin_settings
from tests.webapp_support import (  # noqa: F401 - the fixtures are autouse
    _isolated_backend,
    _offline_resolver,
)
from webapp import __version__, updates
from webapp import app as app_module
from webapp.app import create_app
from webapp.redis_backend import create_backend

JSON = {**FORWARDED, "accept": "application/json"}


def _bumped(version: str) -> str:
    major, minor, patch = (int(part) for part in version.split("."))
    return f"{major}.{minor}.{patch + 1}"


def _bundle(version: str, extra: tarfile.TarInfo | None = None) -> bytes:
    top = f"{updates.BUNDLE_NAME}-{version}"
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, body in (
            (f"{top}/webapp/__init__.py", b""),
            (f"{top}/pyproject.toml", f'version = "{version}"\n'.encode()),
        ):
            info = tarfile.TarInfo(name)
            info.size = len(body)
            archive.addfile(info, io.BytesIO(body))
        if extra is not None:
            archive.addfile(extra, io.BytesIO(b""))
    return buffer.getvalue()


@pytest.fixture
def github(monkeypatch):
    """GitHub, offline: a newer release, its bundle, and a record of restarts."""
    newer = _bumped(__version__)
    state = {"latest": newer, "bundle": _bundle(newer), "verify": None, "restarts": []}
    monkeypatch.setattr(updates, "_fetch_latest", lambda: state["latest"])
    monkeypatch.setattr(updates, "_download", lambda url: state["bundle"])

    def verify(content, **pins):
        state["pins"] = pins
        if isinstance(state["verify"], Exception):
            raise state["verify"]
        return state["verify"]

    monkeypatch.setattr(data_signing, "verify", verify)

    async def no_restart(tree):
        state["restarts"].append(tree)

    monkeypatch.setattr(app_module, "_restart_soon", no_restart)
    return state


def test_is_newer_compares_plain_releases_only():
    """A pre-release or an older version must never be offered as an update."""
    assert updates.is_newer("1.2.4", "1.2.3")
    assert updates.is_newer("1.10.0", "1.9.9")
    assert not updates.is_newer("1.2.3", "1.2.3")
    assert not updates.is_newer("1.2.2", "1.2.3")
    assert not updates.is_newer("2.0.0rc1", "1.2.3")
    assert not updates.is_newer(None, "1.2.3")


def test_a_verified_release_is_unpacked_and_the_process_restarts_on_it(github, tmp_path):
    """The button installs what GitHub named, pinned to the release workflow."""
    app = create_app(_admin_settings(update_check=True, admin_update_dir=str(tmp_path)))
    with TestClient(app) as client:
        page = client.get("/admin", headers=FORWARDED)
        assert github["latest"] in page.text
        assert 'action="/admin/update"' in page.text

        answer = client.post("/admin/update", headers=JSON)

    assert answer.json() == {"state": "requested", "action": "update"}
    tree = tmp_path / f"{updates.BUNDLE_NAME}-{github['latest']}"
    assert (tree / "webapp" / "__init__.py").is_file()
    assert github["restarts"] == [tree]
    assert github["pins"]["workflow"] == ".github/workflows/publish-pypi.yml"
    assert github["pins"]["ref"] == "refs/heads/main"


@pytest.mark.parametrize(
    "outcome",
    [
        data_signing.VerificationSkipped("no attestation has been published"),
        data_signing.SignatureInvalid("signed by somebody else"),
    ],
)
def test_an_unverified_bundle_is_refused_and_nothing_restarts(github, tmp_path, outcome):
    """Unverified is a refusal, not a warning: this is code about to run."""
    github["verify"] = outcome
    app = create_app(_admin_settings(update_check=True, admin_update_dir=str(tmp_path)))
    with TestClient(app) as client:
        answer = client.post("/admin/update", headers=JSON)

    assert answer.json()["state"] == "failed"
    assert github["restarts"] == []
    assert not list(tmp_path.glob(f"{updates.BUNDLE_NAME}-*"))


def test_a_bundle_with_a_link_or_a_stray_path_is_refused(tmp_path, monkeypatch):
    """Only plain files under the one top directory are ever unpacked."""
    version = _bumped(__version__)
    monkeypatch.setattr(data_signing, "verify", lambda content, **pins: None)
    for extra in (tarfile.TarInfo("../escape.py"), tarfile.TarInfo(f"{updates.BUNDLE_NAME}-{version}/link")):
        if extra.name.endswith("link"):
            extra.type = tarfile.SYMTYPE
            extra.linkname = "/etc/passwd"
        bundle = _bundle(version, extra)
        monkeypatch.setattr(updates, "_download", lambda url, bundle=bundle: bundle)
        with pytest.raises(updates.UpdateError):
            updates.install(version, str(tmp_path))
    assert not (tmp_path.parent / "escape.py").exists()


def test_without_an_update_directory_the_area_only_reports_the_release(github):
    """No tmpfs to unpack onto, no button."""
    with TestClient(create_app(_admin_settings(update_check=True))) as client:
        page = client.get("/admin", headers=FORWARDED)
        assert 'action="/admin/update"' not in page.text
        assert client.post("/admin/update", headers=JSON).json()["state"] == "disabled"
    assert github["restarts"] == []


def test_nothing_is_installed_when_the_running_release_is_the_newest(github, tmp_path):
    """Restarting on the running version would be downtime for nothing."""
    github["latest"] = __version__
    app = create_app(_admin_settings(update_check=True, admin_update_dir=str(tmp_path)))
    with TestClient(app) as client:
        assert client.post("/admin/update", headers=JSON).json()["state"] == "current"
    assert github["restarts"] == []
    assert not list(tmp_path.iterdir())


def test_the_update_route_is_absent_for_a_stranger(github, tmp_path):
    """Only the operator the outpost vouches for may install anything."""
    app = create_app(_admin_settings(admin_update_dir=str(tmp_path)))
    with TestClient(app) as client:
        assert client.post("/admin/update").status_code == 404
    assert github["restarts"] == []


def test_a_worker_follows_once_and_never_retries_a_version(github, tmp_path):
    """A release that crashed a worker must not put it in a restart loop."""
    settings = _admin_settings(admin_update_dir=str(tmp_path))

    async def run() -> tuple[Path | None, Path | None, Path | None]:
        backend = create_backend(settings.redis_url)
        before = await updates.follow_update(backend, settings)
        await backend.set(updates.TARGET_KEY, github["latest"], ex=60)
        first = await updates.follow_update(backend, settings)
        again = await updates.follow_update(backend, settings)
        return before, first, again

    before, first, again = asyncio.run(run())
    assert before is None
    assert first is not None and first.name.endswith(github["latest"])
    assert again is None
