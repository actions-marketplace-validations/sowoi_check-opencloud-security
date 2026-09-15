"""Run blocking probes in a process whose lifetime belongs to one ARQ job."""

from __future__ import annotations

import asyncio
import logging
import multiprocessing
from multiprocessing.connection import Connection
from typing import Any

from opencloud_local_scan import ScanError

from .runner import execute_scan
from .ssrf import TargetRejected


def _execute(channel: Connection, arguments: tuple[Any, ...]) -> None:
    # The parent logs lifecycle markers. Scanner exceptions and diagnostics
    # may contain a target or response content, neither of which is a log.
    logging.disable(logging.CRITICAL)
    message: tuple[str, Any]
    try:
        try:
            message = ("completed", execute_scan(*arguments))
        except TargetRejected as exc:
            message = ("rejected", str(exc))
        except ScanError as exc:
            message = ("failed", str(exc))
        except Exception:
            message = ("error", None)
        channel.send(message)
    finally:
        channel.close()


async def execute_scan_process(*arguments: Any, timeout: float) -> dict[str, Any]:
    """Reap the scan, including all probe threads, before releasing its slot."""
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=_execute, args=(sender, arguments), daemon=True)
    started = False
    try:
        process.start()
        started = True
        sender.close()
        # A pipe owned solely by our child, never an external pickle input.
        state, result = await asyncio.wait_for(
            asyncio.to_thread(receiver.recv), timeout=timeout,
        )
        if state == "rejected":
            raise TargetRejected(result)
        if state == "failed":
            raise ScanError(result)
        if state != "completed" or not isinstance(result, dict):
            raise RuntimeError("The scan process failed")
        return result
    finally:
        if started:
            # A thread timeout only stops waiting: its sockets keep running.
            # Kill even on cancellation, then reap before ARQ takes another job.
            if process.is_alive():
                process.kill()
            process.join()
        receiver.close()
        sender.close()
        process.close()
