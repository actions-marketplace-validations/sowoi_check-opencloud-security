"""
Whether a newer release of this service exists, and switching to it.

**Reading is one cached question to GitHub.** The newest published release
of the repository is asked for at most every :data:`CHECK_TTL_SECONDS`, for
the operator's area only. ``COS_WEB_UPDATE_CHECK=false`` turns it off for a
deployment with no outbound access.

**Updating is volatile, and runs in place.** The container stays read-only:
the button downloads that release's web bundle - the same
``check_opencloud_security_web.tar.gz`` the release attaches - verifies its
Sigstore build attestation names this repository's release workflow
(``publish-pypi.yml`` on ``main``) as the signer, refuses it when that cannot
be shown, unpacks it onto the tmpfs named
by ``COS_WEB_ADMIN_UPDATE_DIR`` and replaces the running process with the
same command, started from the unpacked tree. The worker containers follow
within a minute through a Redis key. Nothing is written to the image, so a
container restart is back on the release its image carries. See ADR 0070.

**A release that does not start is not retried.** Each process records the
attempt before it switches; a new tree that fails to import crashes the
process, the container restarts on the image, and that version is then left
alone rather than tried in a loop.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import logging
import os
import re
import shutil
import socket
import sys
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any

import requests

from opencloud_local_scan import data_signing

from . import __version__
from .redis_backend import RedisBackend, RedisUnavailable
from .settings import WebSettings

LOGGER = logging.getLogger("check_opencloud.web.updates")

OWNER = "sowoi"
REPO = "check-opencloud-security"
REPOSITORY = f"{OWNER}/{REPO}"
#: The one workflow allowed to have built a bundle this service will run.
RELEASE_WORKFLOW = ".github/workflows/publish-pypi.yml"
RELEASE_REF = "refs/heads/main"
LATEST_URL = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
BUNDLE_NAME = "check_opencloud_security_web"
BUNDLE_URL = (
    f"https://github.com/{REPOSITORY}/releases/download/v{{version}}/{BUNDLE_NAME}.tar.gz"
)
TIMEOUT_SECONDS = 20
#: A bundle is about 5 MB; anything far larger is not one.
MAX_BUNDLE_BYTES = 64 * 1024 * 1024

#: How long an answer from GitHub is believed.
CHECK_TTL_SECONDS = 6 * 60 * 60
#: How long a failed lookup is remembered, so GitHub is not asked on every load.
FAILURE_TTL_SECONDS = 15 * 60

_CHECK_KEY = "admin:update:latest"
#: The version every process should switch to; short-lived, because the
#: switch is volatile and a restarted container must stay on its image.
TARGET_KEY = "admin:update:target"
TARGET_TTL_SECONDS = 10 * 60
_ATTEMPT_KEY = "admin:update:attempt:{host}:{version}"

_VERSION = re.compile(r"^\d+\.\d+\.\d+$")


class UpdateError(Exception):
    """The release could not be fetched, verified or unpacked."""


def _parse(version: str) -> tuple[int, ...] | None:
    if not _VERSION.match(version):
        return None
    return tuple(int(part) for part in version.split("."))


def is_newer(candidate: str | None, running: str = __version__) -> bool:
    """Whether ``candidate`` is a later plain release than ``running``."""
    if not candidate:
        return False
    new, old = _parse(candidate), _parse(running)
    return new is not None and old is not None and new > old


def _fetch_latest() -> str | None:
    """The newest published release on GitHub, without its ``v``."""
    try:
        response = requests.get(
            LATEST_URL,
            timeout=TIMEOUT_SECONDS,
            headers={"Accept": "application/vnd.github+json"},
        )
        response.raise_for_status()
        tag = response.json().get("tag_name")
    except (requests.RequestException, ValueError, AttributeError) as exc:
        LOGGER.info("update_check_failed error=%s", exc)
        return None
    version = str(tag or "").removeprefix("v")
    return version if _parse(version) else None


async def latest_version(backend: RedisBackend, settings: WebSettings) -> str | None:
    """The newest published release, from the cache or from GitHub."""
    if not settings.update_check:
        return None
    try:
        cached = await backend.get(_CHECK_KEY)
    except RedisUnavailable:
        cached = None
    if cached is not None:
        return cached or None

    version = await asyncio.to_thread(_fetch_latest)
    try:
        await backend.set(
            _CHECK_KEY,
            version or "",
            ex=CHECK_TTL_SECONDS if version else FAILURE_TTL_SECONDS,
        )
    except RedisUnavailable:
        pass
    LOGGER.info("update_check latest=%s running=%s", version, __version__)
    return version


async def update_state(backend: RedisBackend, settings: WebSettings) -> dict[str, Any]:
    """Everything the update card shows."""
    latest = await latest_version(backend, settings)
    return {
        "running": __version__,
        "latest": latest,
        "checked": settings.update_check,
        "available": is_newer(latest),
        "automatic": bool(settings.admin_update_dir),
    }


# ------------------------------------------------------------ the switch


def _download(url: str) -> bytes:
    response = requests.get(url, timeout=TIMEOUT_SECONDS, stream=True)
    response.raise_for_status()
    body = io.BytesIO()
    for chunk in response.iter_content(64 * 1024):
        body.write(chunk)
        if body.tell() > MAX_BUNDLE_BYTES:
            raise UpdateError("the download is larger than any bundle")
    return body.getvalue()


def _safe_members(archive: tarfile.TarFile, top: str) -> list[tarfile.TarInfo]:
    """Regular files and directories under the bundle's one top directory."""
    members = []
    for member in archive.getmembers():
        path = PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts or path.parts[:1] != (top,):
            raise UpdateError(f"unexpected path in the bundle: {member.name}")
        if not (member.isfile() or member.isdir()):
            raise UpdateError(f"unexpected entry in the bundle: {member.name}")
        members.append(member)
    return members


def _verify(bundle: bytes, base: Path) -> None:
    """Refuse a bundle this project's release workflow did not attest.

    A checksum from the same release would only prove the download is
    intact; the attestation proves who built it. Unlike the reference-data
    refresh, *not verified* is a refusal here too - this is code about to run.
    """
    # Sigstore keeps its trust root in the user's cache and data directories;
    # the container is read-only, so both live on the update tmpfs.
    os.environ.setdefault("XDG_CACHE_HOME", str(base / ".cache"))
    os.environ.setdefault("XDG_DATA_HOME", str(base / ".data"))
    try:
        skipped = data_signing.verify(
            bundle,
            owner=OWNER,
            repo=REPO,
            workflow=RELEASE_WORKFLOW,
            ref=RELEASE_REF,
        )
    except data_signing.SignatureInvalid as exc:
        raise UpdateError(str(exc)) from exc
    if skipped is not None:
        raise UpdateError(f"the bundle could not be verified: {skipped.reason}")
    LOGGER.info("update_verified digest=%s", hashlib.sha256(bundle).hexdigest())


def install(version: str, directory: str) -> Path:
    """Fetch, verify and unpack ``version``; return the unpacked tree.

    Already unpacked is returned as it is, so the web process and a worker
    sharing nothing still each end up with the same tree.
    """
    if _parse(version) is None:
        raise UpdateError(f"not a release version: {version!r}")
    base = Path(directory)
    top = f"{BUNDLE_NAME}-{version}"
    tree = base / top
    if (tree / "webapp" / "__init__.py").is_file():
        return tree

    url = BUNDLE_URL.format(version=version)
    try:
        bundle = _download(url)
    except requests.RequestException as exc:
        raise UpdateError(f"download failed: {exc}") from exc
    _verify(bundle, base)

    staging = base / f".{top}.partial"
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(bundle), mode="r:gz") as archive:
        members = _safe_members(archive, top)
        # Every member was checked above: plain files and directories under
        # the one top directory, no links, no absolute or parent paths.
        archive.extractall(staging, members=members)  # nosec B202
    if not (staging / top / "webapp" / "__init__.py").is_file():
        raise UpdateError("the bundle carries no web application")
    (staging / top).rename(tree)
    shutil.rmtree(staging, ignore_errors=True)
    LOGGER.info("update_installed version=%s", version)
    return tree


def restart_into(tree: Path) -> None:  # pragma: no cover - replaces the process
    """Replace this process with the same command, run from ``tree``.

    The working directory comes first on ``sys.path`` for both ``uvicorn``
    and ``python -m``, so the unpacked ``webapp`` and ``opencloud_local_scan``
    are imported instead of the image's, and ``pyproject.toml`` there is what
    the version is read from.
    """
    for handler in logging.getLogger().handlers:
        handler.flush()
    os.chdir(tree)
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(tree)
    environment.pop("COS_WEB_FRONTEND_DIR", None)
    argv = list(getattr(sys, "orig_argv", [sys.executable, *sys.argv]))
    os.execve(sys.executable, argv, environment)  # nosec B606


async def _first_attempt(backend: RedisBackend, version: str) -> bool:
    """Whether this container has not tried ``version`` before."""
    key = _ATTEMPT_KEY.format(host=socket.gethostname(), version=version)
    try:
        return bool(await backend.set(key, "1", ex=24 * 60 * 60, nx=True))
    except RedisUnavailable:
        return True


async def switch_to(backend: RedisBackend, settings: WebSettings, version: str) -> Path:
    """Install ``version`` and record the attempt; the caller restarts."""
    if not settings.admin_update_dir:
        raise UpdateError("COS_WEB_ADMIN_UPDATE_DIR is not set")
    tree = await asyncio.to_thread(install, version, settings.admin_update_dir)
    await _first_attempt(backend, version)
    return tree


async def request_update(
    backend: RedisBackend, settings: WebSettings, operator: str
) -> tuple[str, Path | None]:
    """Fetch the newest release for this process and tell the workers.

    Returns the outcome - ``requested``, ``current``, ``disabled`` or
    ``failed`` - and, when requested, the tree to restart into once the
    answer has been sent.
    """
    if not settings.admin_update_dir:
        return "disabled", None
    latest = await latest_version(backend, settings)
    if latest is None or not is_newer(latest):
        return "current", None
    try:
        tree = await switch_to(backend, settings, latest)
    except (UpdateError, OSError, tarfile.TarError) as exc:
        LOGGER.warning("admin_update_failed version=%s error=%s", latest, exc)
        return "failed", None
    try:
        await backend.set(TARGET_KEY, latest, ex=TARGET_TTL_SECONDS)
    except RedisUnavailable:
        LOGGER.info("admin_update_target_unavailable")
    LOGGER.info(
        "admin_update_requested version=%s running=%s operator=%s",
        latest,
        __version__,
        operator,
    )
    return "requested", tree


async def follow_update(backend: RedisBackend, settings: WebSettings) -> Path | None:
    """For a worker: the tree to restart into, when the area asked for one."""
    if not settings.admin_update_dir:
        return None
    try:
        target = await backend.get(TARGET_KEY)
    except RedisUnavailable:
        return None
    if not target or not is_newer(target):
        return None
    key = _ATTEMPT_KEY.format(host=socket.gethostname(), version=target)
    try:
        if await backend.get(key):
            return None
    except RedisUnavailable:
        return None
    try:
        return await switch_to(backend, settings, target)
    except (UpdateError, OSError, tarfile.TarError) as exc:
        LOGGER.warning("worker_update_failed version=%s error=%s", target, exc)
        return None
