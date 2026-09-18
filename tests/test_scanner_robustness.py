"""
The scanner against a target that answers badly.

A scan runs against whatever address a stranger typed, so the far end is
not trusted to be OpenCloud, to be well-formed, or to answer at all. Every
one of these must end in a :class:`ScanError` - which the plugin turns into
UNKNOWN and the web application into a failed scan - and never in some
other exception, a hang, or a rating built on garbage.
"""

from __future__ import annotations

import socket
import threading
import time
from collections.abc import Iterator

import pytest

from opencloud_local_scan import ScannerSettings, scan
from opencloud_local_scan.scanner import ScanError
from tests.fake_opencloud import FakeOpenCloud, InstanceBehaviour
from tests.test_local_scanner import NO_UPDATES, SETTINGS, run_scan


@pytest.mark.parametrize(
    ("status", "body"),
    [
        (200, b""),
        (200, b"{"),
        (200, b'{"version": '),
        (200, b"null"),
        (200, b"[]"),
        (200, b'"OpenCloud"'),
        (200, b"42"),
        (200, b'{"unrelated": true}'),
        (200, b"\xff\xfe\x00garbage\x80\x81"),
        (200, b"\xef\xbb\xbf<?xml version='1.0'?><status/>"),
        (500, b'{"version": "3.0.0", "productname": "OpenCloud"}'),
        (502, b"<html>Bad Gateway</html>"),
        (503, b""),
        (401, b"unauthorised"),
    ],
)
def test_a_status_answer_that_is_not_an_opencloud_status_is_a_scan_error(status, body):
    """Malformed, empty, non-object, binary or failing status answers are refused, not rated."""
    behaviour = InstanceBehaviour(status_body=body, status_status_code=status)

    with pytest.raises(ScanError):
        run_scan(behaviour)


def test_a_well_formed_status_is_still_scanned():
    """The negative case: the same path with a real status document yields a rating."""
    result = run_scan(InstanceBehaviour())

    assert isinstance(result["rating"], int)


def test_an_endless_status_body_is_cut_off_at_the_cap():
    """A body far larger than the cap is truncated and refused rather than read into memory."""
    capped = ScannerSettings(
        scheme="http",
        timeout=3,
        check_debug_ports=False,
        include_bundled_db=True,
        max_response_bytes=1024,
    )
    behaviour = InstanceBehaviour(status_body=b'{"version": "' + b"9" * (4 * 1024 * 1024) + b'"}')

    with pytest.raises(ScanError):
        run_scan(behaviour, capped)


@pytest.mark.parametrize(
    "capabilities",
    [
        {},
        {"ocs": None},
        {"ocs": []},
        {"ocs": {"data": "not a mapping"}},
        {"ocs": {"data": {"capabilities": None}}},
        {"ocs": {"data": {"capabilities": {"files_sharing": "yes"}}}},
        {"ocs": {"data": {"capabilities": {"files_sharing": {"public": {"password": []}}}}}},
        {"ocs": {"data": {"capabilities": {"password_policy": {"min_characters": "twelve"}}}}},
    ],
)
def test_a_capabilities_document_of_the_wrong_shape_does_not_break_the_scan(capabilities):
    """The capabilities feed optional checks; a wrong shape leaves them out, the scan still finishes."""
    result = run_scan(InstanceBehaviour(capabilities=capabilities))

    assert isinstance(result["rating"], int)
    assert result["product"] == "OpenCloud"


class _SilentServer:
    """Accepts connections and never answers a byte."""

    def __init__(self) -> None:
        self._listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listener.bind(("127.0.0.1", 0))
        self._listener.listen(16)
        self.port = self._listener.getsockname()[1]
        self._held: list[socket.socket] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._accept, daemon=True)

    def _accept(self) -> None:
        self._listener.settimeout(0.1)
        while not self._stop.is_set():
            try:
                connection, _ = self._listener.accept()
            except OSError:
                continue
            self._held.append(connection)

    def __enter__(self) -> _SilentServer:  # noqa: PYI034 - Self needs 3.11
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        self._thread.join(2)
        for connection in self._held:
            connection.close()
        self._listener.close()


@pytest.fixture
def silent() -> Iterator[_SilentServer]:
    with _SilentServer() as server:
        yield server


def test_a_target_that_never_answers_fails_within_the_timeout(silent):
    """A server that accepts and stays silent costs a bounded wait, then a scan error - never a hang."""
    quick = ScannerSettings(scheme="http", timeout=1, check_debug_ports=False, include_bundled_db=True)
    started = time.monotonic()

    with pytest.raises(ScanError):
        scan(f"127.0.0.1:{silent.port}", settings=quick, release_settings=NO_UPDATES)

    # Retries may add a few timeouts, but not an open-ended wait.
    assert time.monotonic() - started < 20


@pytest.mark.parametrize(
    "target",
    ["", " ", "http://", "://", "http://[::1", "127.0.0.1:99999", "127.0.0.1:-1", "exa mple.invalid"],
)
def test_an_address_that_cannot_be_an_address_is_a_scan_error(target):
    """Nonsense in the target is refused as a scan failure, not raised as a parsing exception."""
    with pytest.raises(ScanError):
        scan(target, settings=SETTINGS, release_settings=NO_UPDATES)


def test_a_redirect_loop_on_the_status_path_ends():
    """A status path that redirects to itself forever is given up on, not followed without end."""
    behaviour = InstanceBehaviour(openid_redirect=False)
    with FakeOpenCloud(behaviour) as instance:
        loop = f"http://{instance.host}/status.php"
        behaviour.status_status_code = 302
        behaviour.status_body = b""
        behaviour.extra_headers["Location"] = loop
        started = time.monotonic()
        with pytest.raises(ScanError):
            scan(instance.host, settings=SETTINGS, release_settings=NO_UPDATES)
        assert time.monotonic() - started < 20
