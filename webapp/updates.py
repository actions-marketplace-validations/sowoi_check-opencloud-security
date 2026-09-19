"""
Whether a newer release of this service exists, and asking for it.

**Reading is one cached question to PyPI.** The web service never ships to
PyPI, but the plugin does, and both are released together from the same
``pyproject.toml`` version - so the newest package version there is the
newest release of this service too. The answer is kept in Redis for
:data:`CHECK_TTL_SECONDS`, so however often the operator's area is opened, the
deployment asks at most a few times a day. ``COS_WEB_UPDATE_CHECK=false``
turns the question off for a deployment with no outbound access.

**Updating is a request, never an action.** This process runs read-only,
unprivileged and without the Docker socket, and that stays true: it cannot
replace itself and must not be able to. With ``COS_WEB_ADMIN_UPDATE_DIR`` set,
the button writes one file there naming the version asked for; the separate
``updater`` service in ``docker-compose.dockerhub.yml`` - the one container
with the socket, on no network - reads it, pulls the published image and
recreates the web and worker containers. Nothing written here can choose an
image, a command or a container: the file carries a version string the
updater checks against a fixed pattern and only logs. See ADR 0070.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any

from opencloud_local_scan.selfupdate import _fetch_latest

from . import __version__
from .redis_backend import RedisBackend, RedisUnavailable
from .settings import WebSettings

LOGGER = logging.getLogger("check_opencloud.web.updates")

#: The package whose newest version is this service's newest release.
PACKAGE = "check-opencloud-security"

#: How long an answer from PyPI is believed.
CHECK_TTL_SECONDS = 6 * 60 * 60

#: How long a failed lookup is remembered, so an unreachable PyPI is not
#: asked again on every page load.
FAILURE_TTL_SECONDS = 15 * 60

_CHECK_KEY = "admin:update:latest"

#: The file the updater service watches, and the one it answers in.
REQUEST_FILE = "request"
STATUS_FILE = "status"

_VERSION = re.compile(r"^\d+\.\d+\.\d+$")


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


async def latest_version(backend: RedisBackend, settings: WebSettings) -> str | None:
    """The newest published release, from the cache or from PyPI."""
    if not settings.update_check:
        return None
    try:
        cached = await backend.get(_CHECK_KEY)
    except RedisUnavailable:
        cached = None
    if cached is not None:
        value = cached.decode() if isinstance(cached, bytes) else str(cached)
        return value or None

    version = await asyncio.to_thread(_fetch_latest, PACKAGE, 5.0)
    if version is not None and _parse(version) is None:
        # A pre-release or anything else unexpected is not an update target.
        version = None
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


def _read_status(directory: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads((directory / STATUS_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return raw if isinstance(raw, dict) else None


async def update_state(backend: RedisBackend, settings: WebSettings) -> dict[str, Any]:
    """Everything the update card shows."""
    latest = await latest_version(backend, settings)
    directory = settings.admin_update_dir
    pending = False
    status = None
    if directory:
        path = Path(directory)
        pending = await asyncio.to_thread((path / REQUEST_FILE).exists)
        status = await asyncio.to_thread(_read_status, path)
    return {
        "running": __version__,
        "latest": latest,
        "checked": settings.update_check,
        "available": is_newer(latest),
        "automatic": bool(directory),
        "pending": pending,
        "status": status,
    }


def _write_request(directory: Path, version: str, requested_by: str) -> None:
    target = directory / REQUEST_FILE
    temporary = directory / f".{REQUEST_FILE}.tmp"
    temporary.write_text(
        json.dumps(
            {
                "version": version,
                "requestedBy": requested_by,
                "requestedAt": int(time.time()),
            }
        ),
        encoding="utf-8",
    )
    # Renamed into place, so the updater never reads half a file.
    os.replace(temporary, target)


async def request_update(
    backend: RedisBackend, settings: WebSettings, operator: str
) -> str:
    """Ask the updater for the newest release.

    Returns ``requested``, ``current`` (nothing newer to install),
    ``disabled`` (no updater configured), ``pending`` (already asked) or
    ``failed`` (the request could not be written).
    """
    directory = settings.admin_update_dir
    if not directory:
        return "disabled"
    latest = await latest_version(backend, settings)
    if latest is None or not is_newer(latest):
        return "current"
    path = Path(directory)
    if await asyncio.to_thread((path / REQUEST_FILE).exists):
        return "pending"
    try:
        await asyncio.to_thread(_write_request, path, latest, operator)
    except OSError as exc:
        LOGGER.warning("admin_update_request_failed error=%s", exc)
        return "failed"
    LOGGER.info("admin_update_requested version=%s running=%s", latest, __version__)
    return "requested"
