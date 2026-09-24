"""The scan child process: what crosses the pipe, and how the worker reads it."""

from __future__ import annotations

import asyncio
import logging
import multiprocessing
from multiprocessing.connection import Connection
from typing import cast

import pytest

from opencloud_local_scan import ScanError
from webapp import scan_process
from webapp.ssrf import TargetRejected

# The children below run in a spawned process, so they are module-level
# functions the child can import by name, as `_execute` itself is.


def _child_completed(channel, arguments):
    channel.send(("completed", {"rating": "A"}))
    channel.close()


def _child_rejected(channel, arguments):
    channel.send(("rejected", "target is a private address"))
    channel.close()


def _child_failed(channel, arguments):
    channel.send(("failed", "connection refused"))
    channel.close()


def _child_crashed(channel, arguments):
    channel.send(("error", None))
    channel.close()


def _child_completed_without_a_result(channel, arguments):
    channel.send(("completed", "not a result document"))
    channel.close()


def _run(monkeypatch, child):
    """Run execute_scan_process with `child` in place of the real scan."""
    monkeypatch.setattr(scan_process, "_execute", child)

    async def scenario():
        before = {process.pid for process in multiprocessing.active_children()}
        try:
            return await scan_process.execute_scan_process(timeout=30)
        finally:
            after = {process.pid for process in multiprocessing.active_children()}
            assert after <= before

    return asyncio.run(scenario())


def test_a_completed_scan_returns_its_result_document(monkeypatch):
    """The positive case: a finished scan reaches the worker unchanged."""
    assert _run(monkeypatch, _child_completed) == {"rating": "A"}


def test_a_rejected_target_stays_a_rejection_in_the_worker(monkeypatch):
    """The SSRF guard's refusal must reach the job as a refusal, not as a scan error."""
    with pytest.raises(TargetRejected, match="private address"):
        _run(monkeypatch, _child_rejected)


def test_a_failed_scan_stays_a_scan_error_in_the_worker(monkeypatch):
    """An unreachable target is an ordinary scan failure the user is told about."""
    with pytest.raises(ScanError, match="connection refused") as raised:
        _run(monkeypatch, _child_failed)

    assert not isinstance(raised.value, TargetRejected)


@pytest.mark.parametrize("child", [_child_crashed, _child_completed_without_a_result])
def test_a_crash_or_malformed_answer_is_a_generic_failure(monkeypatch, child):
    """A crash must never be mistaken for a result, and carries no child detail."""
    with pytest.raises(RuntimeError, match="^The scan process failed$"):
        _run(monkeypatch, child)


class _Channel:
    """The sending end of the pipe, recorded in-process."""

    def __init__(self) -> None:
        self.sent: list = []
        self.closed = False

    def send(self, message) -> None:
        self.sent.append(message)

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def child(monkeypatch):
    """Run `_execute` in this process with a scripted scan outcome."""
    outcome: dict = {}

    def execute_scan(*arguments):
        outcome["arguments"] = arguments
        if isinstance(outcome.get("raise"), BaseException):
            raise outcome["raise"]
        return {"rating": "B"}

    monkeypatch.setattr(scan_process, "execute_scan", execute_scan)

    def run():
        channel = _Channel()
        try:
            scan_process._execute(cast(Connection, channel), ("https://opencloud.example.com",))
        finally:
            # _execute silences logging for the rest of the child's life;
            # this process is the test runner and must get it back.
            logging.disable(logging.NOTSET)
        return channel

    return outcome, run


def test_the_child_sends_the_result_and_closes_the_pipe(child):
    """The worker waits on the pipe; an unclosed one is a hung job."""
    outcome, run = child

    channel = run()

    assert channel.sent == [("completed", {"rating": "B"})]
    assert channel.closed
    assert outcome["arguments"] == ("https://opencloud.example.com",)


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (TargetRejected("private address"), ("rejected", "private address")),
        (ScanError("connection refused"), ("failed", "connection refused")),
    ],
)
def test_the_child_names_a_rejection_and_a_scan_failure(child, error, expected):
    """The two expected failures cross the pipe with their message and kind."""
    outcome, run = child
    outcome["raise"] = error

    channel = run()

    assert channel.sent == [expected]
    assert channel.closed


def test_an_unexpected_crash_crosses_the_pipe_without_its_detail(child):
    """An exception text may carry a target or response content, so none is sent."""
    outcome, run = child
    outcome["raise"] = ValueError("secret response body from opencloud.example.com")

    channel = run()

    assert channel.sent == [("error", None)]
    assert channel.closed


def test_the_child_silences_logging(child, monkeypatch):
    """Scanner diagnostics may contain response content and must not reach the logs."""
    _outcome, run = child
    seen: list[bool] = []

    def execute_scan(*arguments):
        seen.append(logging.getLogger("opencloud_local_scan").isEnabledFor(logging.CRITICAL))
        return {"rating": "B"}

    monkeypatch.setattr(scan_process, "execute_scan", execute_scan)
    run()

    assert seen == [False]
    assert logging.getLogger("opencloud_local_scan").isEnabledFor(logging.CRITICAL)
